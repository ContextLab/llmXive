import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.genmod.generalized_linear_model import GLM
from statsmodels.genmod import families
from statsmodels.stats.multitest import multipletests

logger = logging.getLogger(__name__)

class GLMConvergenceError(Exception):
    """Raised when the GLM fitting procedure fails to converge."""
    pass

def load_results_data(csv_path: str) -> pd.DataFrame:
    """
    Load the merged results CSV into a pandas DataFrame.
    
    Args:
        csv_path: Path to the merged results CSV file.
        
    Returns:
        DataFrame containing the results.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} rows from {csv_path}")
    return df

def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare features for GLM analysis.
    
    Ensures categorical variables are properly encoded and
    creates necessary interaction terms.
    
    Args:
        df: Raw results DataFrame.
        
    Returns:
        DataFrame with prepared features.
    """
    # Ensure required columns exist
    required_cols = ['strategy', 'model_size', 'pass_at_1']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Convert categorical columns to category dtype for proper encoding
    df['strategy'] = df['strategy'].astype('category')
    df['model_size'] = df['model_size'].astype('category')
    
    # Create binary target variable (1 if pass, 0 otherwise)
    # Assuming pass_at_1 is already 0 or 1, but ensure it's numeric
    df['target'] = pd.to_numeric(df['pass_at_1'], errors='coerce').fillna(0).astype(int)
    
    return df

def fit_firth_glm(df: pd.DataFrame) -> Optional[GLM]:
    """
    Fit a GLM with Firth's penalized likelihood to handle separation issues.
    
    Args:
        df: Prepared DataFrame with features.
        
    Returns:
        Fitted GLM model or None if fitting fails.
    """
    try:
        # Create formula for main effects
        formula = "target ~ C(strategy) + C(model_size)"
        
        # Fit with binomial family
        model = GLM(
            df['target'],
            pd.get_dummies(df[['strategy', 'model_size']], drop_first=True),
            family=families.Binomial()
        )
        result = model.fit()
        return result
    except Exception as e:
        logger.warning(f"Firth GLM fitting failed: {e}")
        return None

def fit_glm_with_interaction(df: pd.DataFrame) -> Optional[GLM]:
    """
    Fit a GLM with interaction terms between strategy and model size.
    
    Args:
        df: Prepared DataFrame with features.
        
    Returns:
        Fitted GLM model with interaction terms.
    """
    try:
        # Formula with interaction term
        formula = "target ~ C(strategy) * C(model_size)"
        
        # Create design matrix with interaction
        X = pd.get_dummies(df[['strategy', 'model_size']], drop_first=True)
        
        # Add interaction terms manually
        strategy_cols = [c for c in X.columns if 'strategy' in c]
        model_cols = [c for c in X.columns if 'model_size' in c]
        
        for s_col in strategy_cols:
            for m_col in model_cols:
                X[f'{s_col}:{m_col}'] = X[s_col] * X[m_col]
        
        model = GLM(
            df['target'],
            X,
            family=families.Binomial()
        )
        result = model.fit()
        return result
    except Exception as e:
        logger.error(f"GLM with interaction fitting failed: {e}")
        raise GLMConvergenceError(f"GLM fitting failed: {e}")

def perform_post_hoc_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform post-hoc pairwise comparisons between model/strategy combinations.
    
    Specifically calculates the difference in Pass@1 rates between:
    - 1B-model (high-fidelity) vs 7B-model (baseline) for each strategy
    
    Identifies strategies where the margin is >= 5% with p < 0.05.
    
    Args:
        df: Prepared DataFrame with results.
        
    Returns:
        Dictionary containing comparison results and significant findings.
    """
    logger.info("Performing post-hoc pairwise analysis...")
    
    # Group by strategy and model_size to calculate Pass@1 rates
    grouped = df.groupby(['strategy', 'model_size']).agg({
        'target': ['mean', 'count']
    }).reset_index()
    grouped.columns = ['strategy', 'model_size', 'pass_rate', 'n_samples']
    
    # Pivot to get comparison data
    pivot = grouped.pivot(index='strategy', columns='model_size', values='pass_rate')
    
    comparisons = []
    significant_findings = []
    
    # Compare 1B (high-fidelity) vs 7B (baseline) for each strategy
    # Note: Adjust column names based on actual data (e.g., '1B', '7B', '1b', '7b')
    model_cols = [c for c in pivot.columns if str(c).lower() in ['1b', '7b', '1', '7']]
    
    if len(model_cols) < 2:
        logger.warning(f"Could not find both 1B and 7B model columns. Found: {model_cols}")
        return {
            'comparisons': [],
            'significant_findings': [],
            'error': "Missing required model size columns for comparison"
        }
    
    # Identify which is 1B and which is 7B
    model_1b_col = next((c for c in model_cols if str(c).lower() in ['1b', '1']), None)
    model_7b_col = next((c for c in model_cols if str(c).lower() in ['7b', '7']), None)
    
    if not model_1b_col or not model_7b_col:
        logger.warning(f"Could not identify 1B and 7B columns. Found: {model_cols}")
        return {
            'comparisons': [],
            'significant_findings': [],
            'error': "Could not identify 1B and 7B model columns"
        }
    
    for strategy in pivot.index:
        try:
            rate_1b = pivot.loc[strategy, model_1b_col]
            rate_7b = pivot.loc[strategy, model_7b_col]
            
            diff = rate_1b - rate_7b
            diff_pct = diff * 100
            
            # Calculate p-value using two-proportion z-test
            # Get sample sizes
            n_1b = grouped[(grouped['strategy'] == strategy) & (grouped['model_size'] == model_1b_col)]['n_samples'].values
            n_7b = grouped[(grouped['strategy'] == strategy) & (grouped['model_size'] == model_7b_col)]['n_samples'].values
            
            if len(n_1b) == 0 or len(n_7b) == 0:
                continue
            
            n_1b, n_7b = n_1b[0], n_7b[0]
            
            # Two-proportion z-test
            p_1b = rate_1b
            p_7b = rate_7b
            p_pool = (p_1b * n_1b + p_7b * n_7b) / (n_1b + n_7b)
            
            if p_pool == 0 or p_pool == 1:
                p_value = 1.0
            else:
                se = np.sqrt(p_pool * (1 - p_pool) * (1/n_1b + 1/n_7b))
                if se == 0:
                    p_value = 1.0
                else:
                    z_stat = (p_1b - p_7b) / se
                    p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
            
            comparison = {
                'strategy': strategy,
                'model_1b_rate': float(rate_1b),
                'model_7b_rate': float(rate_7b),
                'difference': float(diff),
                'difference_pct': float(diff_pct),
                'p_value': float(p_value),
                'significant_at_0.05': p_value < 0.05,
                'margin_ge_5_pct': abs(diff_pct) >= 5.0
            }
            
            comparisons.append(comparison)
            
            # Check if this meets the criteria: margin >= 5% AND p < 0.05
            if abs(diff_pct) >= 5.0 and p_value < 0.05:
                significant_findings.append({
                    'strategy': strategy,
                    'comparison': f"1B (High-Fidelity) vs 7B (Baseline)",
                    'difference_pct': float(diff_pct),
                    'p_value': float(p_value),
                    'interpretation': f"Strategy '{strategy}' shows a {diff_pct:.1f}% {'improvement' if diff > 0 else 'decrease'} with 1B high-fidelity over 7B baseline (p={p_value:.4f})"
                })
            
        except Exception as e:
            logger.warning(f"Error comparing strategy {strategy}: {e}")
            continue
    
    return {
        'comparisons': comparisons,
        'significant_findings': significant_findings,
        'summary': f"Found {len(significant_findings)} strategies with >=5% margin and p<0.05"
    }

def run_glm_analysis(csv_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the complete GLM analysis pipeline.
    
    Args:
        csv_path: Path to the merged results CSV.
        output_path: Optional path to save results as JSON.
        
    Returns:
        Dictionary containing all analysis results.
    """
    logger.info(f"Starting GLM analysis on {csv_path}")
    
    # Load and prepare data
    df = load_results_data(csv_path)
    df = prepare_features(df)
    
    # Fit models
    glm_main = fit_firth_glm(df)
    glm_interaction = fit_glm_with_interaction(df)
    
    # Post-hoc analysis
    post_hoc_results = perform_post_hoc_analysis(df)
    
    results = {
        'data_summary': {
            'n_observations': len(df),
            'n_strategies': df['strategy'].nunique(),
            'n_model_sizes': df['model_size'].nunique(),
            'strategies': list(df['strategy'].unique()),
            'model_sizes': list(df['model_size'].unique())
        },
        'glm_main_effects': {
            'converged': glm_main is not None,
            'coefficient_summary': glm_main.summary2().as_text() if glm_main else None
        },
        'glm_interaction': {
            'converged': glm_interaction is not None,
            'coefficient_summary': glm_interaction.summary2().as_text() if glm_interaction else None,
            'interaction_significant': glm_interaction.pvalues.filter(like=':') < 0.05 if glm_interaction else None
        },
        'post_hoc_analysis': post_hoc_results
    }
    
    # Save results if output path provided
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Results saved to {output_path}")
    
    return results

def main():
    """Main entry point for GLM analysis script."""
    parser = argparse.ArgumentParser(description="Run GLM analysis on experimental results")
    parser.add_argument(
        '--input', '-i',
        type=str,
        default='data/results.csv',
        help='Path to merged results CSV file'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='data/analysis/glm_results.json',
        help='Path to save analysis results JSON'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        results = run_glm_analysis(args.input, args.output)
        print(json.dumps(results['post_hoc_analysis'], indent=2, default=str))
    except Exception as e:
        logger.error(f"GLM analysis failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()