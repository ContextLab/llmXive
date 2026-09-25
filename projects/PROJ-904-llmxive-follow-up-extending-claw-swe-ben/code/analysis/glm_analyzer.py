"""
GLM Analyzer for Context Fidelity vs. Model Scaling Trade-offs.

Implements Generalized Linear Models with binomial link to test for interaction
effects between context strategy and model size.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.genmod.generalized_linear_model import GLMResults
from statsmodels.genmod.families import Binomial
from statsmodels.genmod.families.links import logit
from statsmodels.stats.power import GofChisquarePower, zt_ind_solve_power

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GLMConvergenceError(Exception):
    """Raised when GLM fitting fails to converge."""
    pass

def load_results_data(input_path: str) -> pd.DataFrame:
    """Load the merged results CSV."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {input_path}")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare features for GLM analysis."""
    # Ensure required columns exist
    required_cols = ['pass', 'model_size', 'strategy', 'task_difficulty', 'quantization_penalty']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Convert categorical variables to dummy variables
    df = pd.get_dummies(df, columns=['model_size', 'strategy'], drop_first=True)
    return df

def fit_firth_glm(formula: str, data: pd.DataFrame) -> GLMResults:
    """
    Fit GLM with Firth's penalized likelihood correction if possible.
    Falls back to standard GLM if Firth is unavailable.
    """
    try:
        # Attempt to use Firth logistic regression if available
        # Note: statsmodels doesn't natively support Firth, so we use a workaround
        # or fallback to standard GLM with warning
        logger.warning("Firth's penalized likelihood not natively available in statsmodels. "
                     "Using standard GLM with binomial family.")
        return fit_glm_with_interaction(formula, data)
    except Exception as e:
        logger.error(f"Firth GLM fitting failed: {e}")
        raise

def fit_glm_with_interaction(formula: str, data: pd.DataFrame) -> GLMResults:
    """Fit standard GLM with interaction terms."""
    try:
        model = sm.GLM.from_formula(
            formula,
            data=data,
            family=Binomial(logit())
        )
        results = model.fit()
        logger.info(f"GLM fitting successful. Log-likelihood: {results.llf}")
        return results
    except Exception as e:
        logger.error(f"GLM fitting failed: {e}")
        raise GLMConvergenceError(f"GLM failed to converge: {e}")

def calculate_pairwise_diff(df: pd.DataFrame, strategy: str) -> Tuple[float, float]:
    """
    Calculate the difference in Pass@1 rates between 1B (high-fidelity) and 7B (baseline)
    for a specific strategy.
    
    Returns: (margin, p_value)
    """
    subset = df[df['strategy'] == strategy]
    if len(subset) == 0:
        return 0.0, 1.0
    
    # Calculate pass rates
    pass_1b = subset[subset['model_size'] == '1B']['pass'].mean()
    pass_7b = subset[subset['model_size'] == '7B']['pass'].mean()
    
    margin = pass_1b - pass_7b
    
    # Simple two-proportion z-test for p-value
    n1 = len(subset[subset['model_size'] == '1B'])
    n2 = len(subset[subset['model_size'] == '7B'])
    
    if n1 == 0 or n2 == 0:
        return margin, 1.0
    
    p_pooled = (subset['pass'].sum()) / len(subset)
    se = np.sqrt(p_pooled * (1 - p_pooled) * (1/n1 + 1/n2))
    
    if se == 0:
        return margin, 1.0
    
    z_stat = margin / se
    # Two-tailed p-value
    p_value = 2 * (1 - sm.stats.norm.cdf(abs(z_stat)))
    
    logger.info(f"Strategy {strategy}: 1B={pass_1b:.3f}, 7B={pass_7b:.3f}, "
               f"margin={margin:.3f}, p={p_value:.3f}")
    
    return margin, p_value

def check_significance(margin: float, p_value: float, threshold_margin: float = 0.05, 
                     threshold_p: float = 0.05) -> bool:
    """
    Check if the result is statistically significant based on thresholds.
    SC-004: margin >= 5% and p < 0.05
    """
    is_significant = (abs(margin) >= threshold_margin) and (p_value < threshold_p)
    logger.info(f"Significance check: margin={margin:.3f} (>= {threshold_margin}), "
               f"p={p_value:.3f} (< {threshold_p}) -> {is_significant}")
    return is_significant

def perform_post_hoc_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """Perform post-hoc analysis for all strategies."""
    results = {}
    strategies = df['strategy'].unique()
    
    for strategy in strategies:
        margin, p_value = calculate_pairwise_diff(df, strategy)
        results[strategy] = {
            'margin': margin,
            'p_value': p_value,
            'significant': check_significance(margin, p_value)
        }
    
    return results

def power_analysis(
    df: pd.DataFrame,
    effect_size: float = 0.3,
    alpha: float = 0.05,
    power_threshold: float = 0.8
) -> Dict[str, Any]:
    """
    Calculate the statistical power of the experiment given the expected effect size
    and sample count.
    
    Args:
        df: The results DataFrame
        effect_size: Expected effect size (Cohen's h for proportions)
        alpha: Significance level
        power_threshold: Minimum acceptable power threshold
        
    Returns:
        Dictionary with power analysis results
    """
    n_total = len(df)
    n_groups = df['model_size'].nunique()
    n_per_group = n_total / n_groups if n_groups > 0 else 0
    
    # Calculate power for two-proportion z-test
    # Using statsmodels power analysis
    try:
        # For two independent proportions, we use zt_ind_solve_power
        # effect_size is Cohen's h
        power = zt_ind_solve_power(
            effect_size=effect_size,
            n1=n_per_group,
            n2=n_per_group,
            alpha=alpha,
            ratio=1.0,
            alternative='two-sided'
        )
    except Exception as e:
        logger.warning(f"Power calculation failed: {e}. Using conservative estimate.")
        power = 0.0
    
    result = {
        'total_samples': int(n_total),
        'samples_per_group': float(n_per_group),
        'effect_size_assumed': effect_size,
        'alpha': alpha,
        'calculated_power': float(power),
        'power_threshold': power_threshold,
        'is_adequate': power >= power_threshold
    }
    
    if power < power_threshold:
        logger.warning(
            f"⚠️  WARNING: Statistical power ({power:.3f}) is below the threshold "
            f"({power_threshold}). This may indicate 'Insufficient Context-Bound Data'. "
            f"Consider increasing sample size or re-evaluating the experiment design."
        )
    else:
        logger.info(
            f"✓ Statistical power ({power:.3f}) meets the threshold ({power_threshold}). "
            f"Sample size appears adequate."
        )
    
    return result

def run_glm_analysis(
    input_path: str,
    output_path: str,
    formula: str = None
) -> Dict[str, Any]:
    """
    Run the full GLM analysis pipeline.
    
    Args:
        input_path: Path to the results CSV
        output_path: Path to save the analysis results JSON
        formula: GLM formula (default includes interaction)
        
    Returns:
        Dictionary with analysis results
    """
    if formula is None:
        formula = "pass ~ model_size + strategy + model_size:strategy + task_difficulty + quantization_penalty"
    
    # Load data
    df = load_results_data(input_path)
    
    # Prepare features
    df_prepared = prepare_features(df)
    
    # Fit GLM
    logger.info(f"Fitting GLM with formula: {formula}")
    glm_results = fit_glm_with_interaction(formula, df_prepared)
    
    # Extract key statistics
    interaction_p_value = None
    for term in glm_results.params.index:
        if 'model_size' in term and 'strategy' in term:
            interaction_p_value = glm_results.pvalues[term]
            break
    
    # Perform post-hoc analysis
    post_hoc = perform_post_hoc_analysis(df)
    
    # Perform power analysis
    power_result = power_analysis(df)
    
    # Compile results
    results = {
        'formula': formula,
        'n_samples': len(df),
        'log_likelihood': float(glm_results.llf),
        'aic': float(glm_results.aic),
        'bic': float(glm_results.bic),
        'interaction_p_value': float(interaction_p_value) if interaction_p_value is not None else None,
        'post_hoc_analysis': post_hoc,
        'power_analysis': power_result,
        'coefficients': {k: float(v) for k, v in glm_results.params.items()},
        'p_values': {k: float(v) for k, v in glm_results.pvalues.items()}
    }
    
    # Save results
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"GLM analysis results saved to {output_path}")
    return results

def main():
    """Main entry point for GLM analysis."""
    parser = argparse.ArgumentParser(description='Run GLM analysis on experiment results')
    parser.add_argument('--input', type=str, required=True, help='Path to results CSV')
    parser.add_argument('--output', type=str, required=True, help='Path to output JSON')
    parser.add_argument('--formula', type=str, default=None, help='GLM formula')
    
    args = parser.parse_args()
    
    try:
        results = run_glm_analysis(args.input, args.output, args.formula)
        logger.info("GLM analysis completed successfully")
    except Exception as e:
        logger.error(f"GLM analysis failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()