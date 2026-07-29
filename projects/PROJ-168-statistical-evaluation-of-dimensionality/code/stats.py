"""
Statistical analysis module for dimensionality reduction evaluation.
Handles ANOVA, Mixed-Effects models, and error recovery strategies.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StatsError(Exception):
    """Custom exception for statistical analysis errors."""
    pass

def load_aggregated_metrics(metrics_path: str) -> pd.DataFrame:
    """
    Load aggregated geometry and fidelity metrics from JSON/CSV.
    
    Args:
        metrics_path: Path to the aggregated metrics file (JSON or CSV).
        
    Returns:
        DataFrame containing the metrics.
        
    Raises:
        StatsError: If file cannot be loaded or is invalid.
    """
    path = Path(metrics_path)
    if not path.exists():
        raise StatsError(f"Metrics file not found: {metrics_path}")
    
    try:
        if path.suffix == '.json':
            with open(path, 'r') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
        elif path.suffix == '.csv':
            df = pd.read_csv(path)
        else:
            raise StatsError(f"Unsupported file format: {path.suffix}")
        
        if df.empty:
            raise StatsError("Metrics file is empty")
            
        return df
    except Exception as e:
        raise StatsError(f"Failed to load metrics: {str(e)}")

def check_collinearity(df: pd.DataFrame, formula: str, threshold: float = 5.0) -> Tuple[bool, float]:
    """
    Check for multicollinearity in the design matrix using VIF.
    
    Args:
        df: DataFrame containing the data.
        formula: Statsmodels formula string.
        threshold: VIF threshold for concern (default 5.0).
        
    Returns:
        Tuple of (is_collinear, max_vif).
        
    Raises:
        StatsError: If VIF calculation fails.
    """
    try:
        # Create design matrix
        design = sm.datasets.tools.categorical(df, drop_first=True)
        # Handle formula parsing manually for VIF
        # Extract RHS variables from formula (after ~)
        rhs = formula.split('~')[1].strip()
        
        # Create a simpler design matrix for VIF
        # This is a simplified approach; in practice, one might use patsy
        import patsy
        y, X = patsy.dmatrices(formula, df, return_type='dataframe')
        
        # Add constant
        X = sm.add_constant(X)
        
        vifs = []
        for col in X.columns:
            if col == 'Intercept':
                continue
            try:
                vif = variance_inflation_factor(X.values, X.columns.get_loc(col))
                vifs.append(vif)
            except Exception as e:
                logger.warning(f"Could not calculate VIF for {col}: {e}")
                vifs.append(np.inf)
        
        max_vif = max(vifs) if vifs else 0
        is_collinear = max_vif >= threshold
        
        return is_collinear, max_vif
        
    except Exception as e:
        logger.error(f"VIF calculation failed: {e}")
        # If we can't calculate VIF, assume collinearity is present to be safe
        return True, np.inf

def fit_fixed_effects_anova(df: pd.DataFrame, formula: str) -> Dict[str, Any]:
    """
    Fit a Fixed-Effects ANOVA model.
    
    Args:
        df: DataFrame with the data.
        formula: Statsmodels formula string.
        
    Returns:
        Dictionary containing model results.
        
    Raises:
        StatsError: If model fitting fails.
    """
    try:
        model = smf.ols(formula, data=df)
        results = model.fit()
        
        # Extract ANOVA table
        anova_table = sm.stats.anova_lm(results, typ=2)
        
        return {
            'model_type': 'Fixed-Effects ANOVA',
            'success': True,
            'f_values': anova_table['F'].to_dict(),
            'p_values': anova_table['PR(>F)'].to_dict(),
            'summary': results.summary().as_text(),
            'params': results.params.to_dict(),
            'rsquared': results.rsquared
        }
    except Exception as e:
        raise StatsError(f"Fixed-Effects ANOVA failed: {str(e)}")

def fit_mixed_effects_model(df: pd.DataFrame, formula: str) -> Dict[str, Any]:
    """
    Fit a Mixed-Effects Linear Model (LMM).
    
    Args:
        df: DataFrame with the data.
        formula: Statsmodels formula string (e.g., 'fidelity ~ method + (1|dataset)').
        
    Returns:
        Dictionary containing model results.
        
    Raises:
        StatsError: If model fitting fails.
    """
    try:
        # Use MixedLM from statsmodels
        # Note: formula parsing for mixed models requires specific syntax
        # We'll use a simplified approach for now
        import patsy
        y, X = patsy.dmatrices(formula, df, return_type='dataframe')
        
        # Identify grouping variable from formula (e.g., (1|dataset))
        import re
        group_match = re.search(r'\(1\|(\w+)\)', formula)
        if not group_match:
            raise StatsError("Could not identify grouping variable in formula")
        group_col = group_match.group(1)
        
        groups = df[group_col]
        
        # Fit MixedLM
        model = sm.MixedLM(y, X, groups=groups)
        results = model.fit()
        
        return {
            'model_type': 'Mixed-Effects Model',
            'success': True,
            'f_values': {}, # MixedLM doesn't directly provide F-values in same way
            'p_values': results.pvalues.to_dict(),
            'summary': results.summary().as_text(),
            'params': results.params.to_dict(),
            'random_effects_params': results.random_effects
        }
    except Exception as e:
        raise StatsError(f"Mixed-Effects model failed: {str(e)}")

def fit_simplified_model(df: pd.DataFrame, formula: str, model_type: str) -> Dict[str, Any]:
    """
    Attempt to fit a simplified version of the model when the full model fails.
    
    Args:
        df: DataFrame with the data.
        formula: Original formula.
        model_type: 'fixed' or 'mixed'.
        
    Returns:
        Dictionary with simplified model results.
    """
    try:
        # Simplify by removing interaction terms or random effects
        simplified_formula = formula.split('+')[0].strip() # Take only the main effect
        
        if model_type == 'mixed':
            # Try fixed effects only
            return fit_fixed_effects_anova(df, simplified_formula)
        else:
            # Try with fewer parameters
            return fit_fixed_effects_anova(df, simplified_formula)
            
    except Exception as e:
        logger.error(f"Simplified model also failed: {e}")
        raise StatsError(f"All model fitting attempts failed: {str(e)}")

def run_interaction_test(df: pd.DataFrame, formula: str, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Run interaction tests and apply Benjamini-Hochberg correction.
    
    Args:
        df: DataFrame with the data.
        formula: Statsmodels formula.
        alpha: Significance level.
        
    Returns:
        Dictionary with test results.
    """
    try:
        model = smf.ols(formula, data=df)
        results = model.fit()
        
        # Get p-values
        p_values = results.pvalues
        
        # Apply Benjamini-Hochberg
        reject, p_corrected, _, _ = multipletests(p_values, alpha=alpha, method='fdr_bh')
        
        return {
            'raw_p_values': p_values.to_dict(),
            'corrected_p_values': p_corrected,
            'rejected': reject.to_dict(),
            'alpha': alpha
        }
    except Exception as e:
        raise StatsError(f"Interaction test failed: {str(e)}")

def apply_benjamini_hochberg(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], List[bool]]:
    """
    Apply Benjamini-Hochberg correction to a list of p-values.
    
    Args:
        p_values: List of p-values.
        alpha: Significance level.
        
    Returns:
        Tuple of (corrected p-values, boolean rejection list).
    """
    if not p_values:
        return [], []
        
    reject, p_corrected, _, _ = multipletests(p_values, alpha=alpha, method='fdr_bh')
    return list(p_corrected), list(reject)

def save_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save statistical analysis results to a JSON file.
    
    Args:
        results: Dictionary of results to save.
        output_path: Path to output file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Results saved to {output_path}")

def run_analysis_with_error_handling(
    df: pd.DataFrame,
    formula: str,
    model_type: str = 'mixed',
    vif_threshold: float = 5.0,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main entry point for running statistical analysis with robust error handling.
    
    This function:
    1. Checks for collinearity (VIF).
    2. Attempts to fit the specified model.
    3. If the model fails, attempts a simplified version.
    4. Records all failures and successes.
    5. Aborts if VIF >= threshold.
    
    Args:
        df: DataFrame with the data.
        formula: Statsmodels formula string.
        model_type: 'fixed' or 'mixed'.
        vif_threshold: VIF threshold for aborting (default 5.0).
        output_path: Optional path to save results.
        
    Returns:
        Dictionary containing the final results and execution log.
        
    Raises:
        StatsError: If VIF >= threshold or all model fitting attempts fail.
    """
    execution_log = {
        'timestamp': pd.Timestamp.now().isoformat(),
        'formula': formula,
        'model_type_requested': model_type,
        'vif_threshold': vif_threshold,
        'steps': []
    }
    
    # Step 1: Check Collinearity
    logger.info("Checking for multicollinearity (VIF)...")
    execution_log['steps'].append({'step': 'vif_check', 'status': 'started'})
    
    try:
        is_collinear, max_vif = check_collinearity(df, formula, vif_threshold)
        execution_log['vif_result'] = {
            'max_vif': float(max_vif),
            'is_collinear': is_collinear
        }
        execution_log['steps'].append({
            'step': 'vif_check', 
            'status': 'completed',
            'max_vif': float(max_vif),
            'is_collinear': is_collinear
        })
        
        if max_vif >= vif_threshold:
            error_msg = f"Multicollinearity detected (VIF={max_vif:.2f} >= {vif_threshold}). ABORTING."
            logger.error(error_msg)
            execution_log['error'] = error_msg
            execution_log['final_status'] = 'ABORTED_VIF'
            
            if output_path:
                save_results(execution_log, output_path)
            
            raise StatsError(error_msg)
            
    except Exception as e:
        error_msg = f"VIF check failed: {str(e)}"
        logger.error(error_msg)
        execution_log['steps'].append({'step': 'vif_check', 'status': 'failed', 'error': str(e)})
        # If we can't check VIF, we proceed but note it
        execution_log['vif_result'] = {'error': str(e), 'assumed_safe': False}
    
    # Step 2: Attempt Primary Model
    logger.info(f"Attempting to fit {model_type} model...")
    execution_log['steps'].append({'step': 'primary_model', 'status': 'started'})
    
    primary_result = None
    try:
        if model_type == 'mixed':
            primary_result = fit_mixed_effects_model(df, formula)
        else:
            primary_result = fit_fixed_effects_anova(df, formula)
        
        if primary_result.get('success'):
            logger.info("Primary model fitted successfully.")
            execution_log['steps'].append({
                'step': 'primary_model', 
                'status': 'completed',
                'model_type': model_type
            })
        else:
            raise StatsError("Primary model returned success=False")
            
    except Exception as e:
        error_msg = f"Primary model failed: {str(e)}"
        logger.warning(error_msg)
        execution_log['steps'].append({
            'step': 'primary_model', 
            'status': 'failed', 
            'error': str(e)
        })
        
        # Step 3: Attempt Simplified Model
        logger.info("Attempting simplified model...")
        execution_log['steps'].append({'step': 'simplified_model', 'status': 'started'})
        
        try:
            simplified_result = fit_simplified_model(df, formula, model_type)
            if simplified_result.get('success'):
                logger.info("Simplified model fitted successfully.")
                execution_log['steps'].append({
                    'step': 'simplified_model', 
                    'status': 'completed',
                    'model_type': 'simplified'
                })
                primary_result = simplified_result
            else:
                raise StatsError("Simplified model returned success=False")
                
        except Exception as e2:
            error_msg = f"All model fitting attempts failed: {str(e2)}"
            logger.error(error_msg)
            execution_log['steps'].append({
                'step': 'simplified_model', 
                'status': 'failed', 
                'error': str(e2)
            })
            execution_log['error'] = error_msg
            execution_log['final_status'] = 'FAILED_ALL_MODELS'
            
            if output_path:
                save_results(execution_log, output_path)
            
            raise StatsError(error_msg)
    
    # Step 4: Compile Final Results
    if primary_result:
        execution_log['final_status'] = 'SUCCESS'
        execution_log['model_results'] = primary_result
      
      # Run interaction test if applicable
        if 'p_values' in primary_result:
            try:
                interaction_results = run_interaction_test(df, formula)
                execution_log['interaction_test'] = interaction_results
            except Exception as e:
                logger.warning(f"Interaction test failed: {e}")
                execution_log['interaction_test'] = {'error': str(e)}
    
    # Save if path provided
    if output_path:
        save_results(execution_log, output_path)
    
    return execution_log

def main():
    """Main entry point for command-line execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run statistical analysis with error handling.')
    parser.add_argument('--metrics', type=str, required=True, help='Path to aggregated metrics file.')
    parser.add_argument('--formula', type=str, default='fidelity ~ method', help='Statsmodels formula.')
    parser.add_argument('--model', type=str, default='mixed', choices=['fixed', 'mixed'], help='Model type.')
    parser.add_argument('--vif-threshold', type=float, default=5.0, help='VIF threshold for abort.')
    parser.add_argument('--output', type=str, default='results/stats_analysis.json', help='Output path.')
    
    args = parser.parse_args()
    
    try:
        logger.info(f"Loading metrics from {args.metrics}...")
        df = load_aggregated_metrics(args.metrics)
        
        logger.info(f"Running analysis with formula: {args.formula}")
        results = run_analysis_with_error_handling(
            df=df,
            formula=args.formula,
            model_type=args.model,
            vif_threshold=args.vif_threshold,
            output_path=args.output
        )
        
        print(json.dumps(results, indent=2, default=str))
        sys.exit(0)
        
    except StatsError as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()