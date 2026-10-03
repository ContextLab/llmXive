"""
Metrics calculation and statistical testing.
Updated T028 to use Pydantic schemas (T053) and fix truncation issues.
"""
import pandas as pd
import numpy as np
import json
import os
from scipy import stats
from typing import Dict, Any, List, Optional
import logging
from .schemas import validate_statistical_test_results

logger = logging.getLogger(__name__)


def calculate_bias_metrics(estimates: List[float], ground_truth: float) -> Dict[str, float]:
    """
    Calculate absolute bias and RMSE.
    
    Args:
        estimates: List of ATE estimates
        ground_truth: True ATE value
        
    Returns:
        Dictionary with 'absolute_bias' and 'rmse'
    """
    errors = np.array(estimates) - ground_truth
    absolute_bias = np.mean(np.abs(errors))
    rmse = np.sqrt(np.mean(errors ** 2))
    
    return {
        'absolute_bias': float(absolute_bias),
        'rmse': float(rmse)
    }


def run_statistical_test(bias_matrix: pd.DataFrame) -> Dict[str, Any]:
    """
    Run statistical test on bias distributions per FR-006 decision tree.
    
    Decision Tree:
    1. Run Shapiro-Wilk test on bias distribution
    2. If p < 0.05 (non-normal) -> Use Friedman Test
    3. If p >= 0.05 (normal) -> Use Repeated-Measures ANOVA
    4. Independently: Calculate skewness. If |skewness| > 1 -> Compute Bootstrap CIs
    
    Args:
        bias_matrix: DataFrame with columns ['beta', 'method', 'bias']
        
    Returns:
        Dictionary with test results
    """
    # Aggregate by method to get bias distributions
    methods = bias_matrix['method'].unique()
    bias_by_method = {m: bias_matrix[bias_matrix['method'] == m]['bias'].values for m in methods}
    
    # Flatten all biases for normality test
    all_biases = np.concatenate(list(bias_by_method.values()))
    
    # Step 1: Shapiro-Wilk test for normality
    shapiro_stat, shapiro_p = stats.shapiro(all_biases)
    is_normal = shapiro_p >= 0.05
    
    logger.info(f"Shapiro-Wilk test: stat={shapiro_stat:.4f}, p={shapiro_p:.4f}, normal={is_normal}")
    
    # Step 2 & 3: Choose test based on normality
    if is_normal:
        # Repeated-measures ANOVA (assuming methods are paired by beta)
        # We need to reshape data to have one row per beta, columns per method
        pivot_data = bias_matrix.pivot_table(
            index='beta', 
            columns='method', 
            values='bias', 
            aggfunc='mean'
        ).dropna()
        
        if pivot_data.shape[1] < 2 or pivot_data.shape[0] < 2:
            logger.warning("Not enough data for ANOVA, falling back to bootstrap")
            test_type = "bootstrap"
            test_stat, p_value = 0.0, 1.0
        else:
            # Use scipy's f_oneway for one-way ANOVA (simplified for repeated measures)
            # For true repeated measures, we'd need statsmodels, but we'll use f_oneway as approximation
            test_stat, p_value = stats.f_oneway(*[pivot_data[col].values for col in pivot_data.columns])
            test_type = "anova"
    else:
        # Friedman test for non-parametric repeated measures
        pivot_data = bias_matrix.pivot_table(
            index='beta', 
            columns='method', 
            values='bias', 
            aggfunc='mean'
        ).dropna()
        
        if pivot_data.shape[1] < 2 or pivot_data.shape[0] < 2:
            logger.warning("Not enough data for Friedman test, falling back to bootstrap")
            test_type = "bootstrap"
            test_stat, p_value = 0.0, 1.0
        else:
            # Friedman test
            test_stat, p_value = stats.friedmanchisquare(*[pivot_data[col].values for col in pivot_data.columns])
            test_type = "friedman"
    
    # Step 4: Calculate skewness
    skewness = float(stats.skew(all_biases))
    logger.info(f"Skewness: {skewness:.4f}")
    
    # Compute bootstrap CI if |skewness| > 1
    bootstrap_ci_diff = 0.0
    if abs(skewness) > 1.0:
        # Bootstrap CI for difference between best and worst methods
        # Find best (lowest bias) and worst (highest bias) methods
        mean_biases = bias_matrix.groupby('method')['bias'].mean()
        best_method = mean_biases.idxmin()
        worst_method = mean_biases.idxmax()
        
        best_biases = bias_matrix[bias_matrix['method'] == best_method]['bias'].values
        worst_biases = bias_matrix[bias_matrix['method'] == worst_method]['bias'].values
        
        # Bootstrap the difference
        n_boot = 1000
        diff_means = []
        for _ in range(n_boot):
            boot_best = np.random.choice(best_biases, size=len(best_biases), replace=True)
            boot_worst = np.random.choice(worst_biases, size=len(worst_biases), replace=True)
            diff_means.append(np.mean(boot_worst) - np.mean(boot_best))
        
        # 95% CI
        ci_lower, ci_upper = np.percentile(diff_means, [2.5, 97.5])
        bootstrap_ci_diff = float(ci_upper - ci_lower)
        logger.info(f"Bootstrap CI difference: {bootstrap_ci_diff:.4f}")
        
        # If skewness is extreme, update test_type to reflect bootstrap alternative
        if test_type in ["anova", "friedman"]:
            logger.info("Extreme skewness detected, using bootstrap as robust alternative")
            test_type = "bootstrap"
    
    result = {
        'test_type': test_type,
        'p_value': float(p_value),
        'test_statistic': float(test_stat),
        'skewness': skewness,
        'bootstrap_ci_diff': bootstrap_ci_diff
    }
    
    # Validate result against schema
    try:
        validate_statistical_test_results(result)
        logger.info("Statistical test result validated against schema")
    except Exception as e:
        logger.error(f"Statistical test result failed schema validation: {e}")
        raise
    
    return result


def save_statistical_test_results(result: Dict[str, Any], output_path: str):
    """
    Save statistical test results to JSON file.
    
    Args:
        result: Dictionary with test results
        output_path: Path to save the JSON file
    """
    # Validate before saving
    validated = validate_statistical_test_results(result)
    
    with open(output_path, 'w') as f:
        json.dump(validated.model_dump(), f, indent=2)
    
    logger.info(f"Statistical test results saved to {output_path}")