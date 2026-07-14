"""
Metrics calculation module for statistical analysis of chess game data.

This module provides functions for calculating statistical metrics,
including Wald Z-tests, F-statistics, and Benjamini-Hochberg FDR correction.
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Any, Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)

def calculate_wald_z_test(
    coefficient: float,
    standard_error: float,
    alternative: str = "two-sided"
) -> Tuple[float, float]:
    """
    Calculate Wald Z-test statistic and p-value for a coefficient.
    
    Args:
        coefficient: The estimated coefficient value.
        standard_error: The standard error of the coefficient.
        alternative: Type of test ("two-sided", "less", "greater").
    
    Returns:
        Tuple of (z_statistic, p_value).
    
    Raises:
        ValueError: If standard_error is zero or negative.
    """
    if standard_error <= 0:
        raise ValueError("Standard error must be positive for Wald test.")
    
    z_stat = coefficient / standard_error
    
    if alternative == "two-sided":
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    elif alternative == "less":
        p_value = stats.norm.cdf(z_stat)
    elif alternative == "greater":
        p_value = 1 - stats.norm.cdf(z_stat)
    else:
        raise ValueError(f"Unknown alternative: {alternative}")
    
    return z_stat, p_value

def calculate_f_statistic(
    model_r_squared: float,
    n_observations: int,
    n_predictors: int
) -> float:
    """
    Calculate F-statistic for a regression model.
    
    Args:
        model_r_squared: R-squared value of the model.
        n_observations: Number of observations in the dataset.
        n_predictors: Number of predictors in the model.
    
    Returns:
        F-statistic value.
    
    Raises:
        ValueError: If inputs are invalid.
    """
    if n_observations <= n_predictors:
        raise ValueError("Number of observations must exceed number of predictors.")
    
    numerator = model_r_squared / n_predictors
    denominator = (1 - model_r_squared) / (n_observations - n_predictors - 1)
    
    if denominator == 0:
        return float('inf') if numerator > 0 else 0.0
    
    return numerator / denominator

def calculate_model_f_statistic(
    rss: float,
    tss: float,
    n_observations: int,
    n_predictors: int
) -> float:
    """
    Calculate F-statistic from Residual Sum of Squares (RSS) and Total Sum of Squares (TSS).
    
    Args:
        rss: Residual Sum of Squares.
        tss: Total Sum of Squares.
        n_observations: Number of observations.
        n_predictors: Number of predictors.
    
    Returns:
        F-statistic value.
    """
    r_squared = 1 - (rss / tss) if tss > 0 else 0.0
    return calculate_f_statistic(r_squared, n_observations, n_predictors)

def apply_benjamini_hochberg_fdr(
    p_values: List[float],
    alpha: float = 0.05,
    method: str = "indep"
) -> Tuple[List[float], List[bool]]:
    """
    Apply Benjamini-Hochberg False Discovery Rate (FDR) correction to p-values.
    
    This function implements the BH procedure for controlling the FDR in
    multiple hypothesis testing. It can handle both independent and
    positively dependent test statistics.
    
    Args:
        p_values: List of raw p-values from hypothesis tests.
        alpha: Significance level (default 0.05).
        method: "indep" for independent tests, "posdep" for positively dependent.
    
    Returns:
        Tuple of (adjusted_p_values, boolean_rejection_mask).
        - adjusted_p_values: FDR-corrected p-values.
        - boolean_rejection_mask: True if the null hypothesis is rejected.
    
    Raises:
        ValueError: If p_values is empty or contains invalid values.
    """
    if not p_values:
        raise ValueError("p_values list cannot be empty.")
    
    p_values = np.array(p_values)
    
    if np.any(p_values < 0) or np.any(p_values > 1):
        raise ValueError("All p-values must be in the range [0, 1].")
    
    n_tests = len(p_values)
    
    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p_values = p_values[sorted_indices]
    
    # Calculate BH critical values
    # For "indep" or "posdep", we use the standard BH procedure
    # The formula is: p(i) <= (i/n) * alpha
    ranks = np.arange(1, n_tests + 1)
    critical_values = (ranks / n_tests) * alpha
    
    # Find the largest k such that p(k) <= critical_value(k)
    # Then reject all hypotheses with p <= p(k)
    # This is equivalent to finding the largest rank where the condition holds
    
    # For adjusted p-values, we use the formula:
    # p_adj(i) = min(1, min_{j >= i} (n/j) * p(j))
    # But implemented in a way that ensures monotonicity
    
    adjusted_p_values = np.zeros(n_tests)
    adjusted_p_values[-1] = min(1.0, sorted_p_values[-1] * n_tests / n_tests)
    
    # Calculate adjusted p-values from largest to smallest
    for i in range(n_tests - 2, -1, -1):
        # The adjusted p-value for the i-th smallest p-value is:
        # min(1, min((n/j)*p(j) for j in [i+1, n]))
        # Which simplifies to: min(1, (n/(i+1))*p(i), adjusted_p_values[i+1])
        # But we need to ensure monotonicity: p_adj[i] <= p_adj[i+1]
        
        candidate = sorted_p_values[i] * n_tests / (i + 1)
        adjusted_p_values[i] = min(1.0, candidate, adjusted_p_values[i + 1])
    
    # Ensure monotonicity in the opposite direction (in case of numerical issues)
    for i in range(1, n_tests):
        adjusted_p_values[i] = max(adjusted_p_values[i], adjusted_p_values[i - 1])
    
    # Map adjusted p-values back to original order
    final_adjusted_p_values = np.zeros(n_tests)
    final_adjusted_p_values[sorted_indices] = adjusted_p_values
    
    # Determine rejections
    rejection_mask = final_adjusted_p_values <= alpha
    
    logger.info(f"Applied Benjamini-Hochberg FDR correction to {n_tests} tests.")
    logger.info(f"Number of rejections at alpha={alpha}: {np.sum(rejection_mask)}")
    
    return final_adjusted_p_values.tolist(), rejection_mask.tolist()

def extract_metrics_from_statsmodels_result(
    result,
    feature_names: List[str]
) -> Dict[str, Any]:
    """
    Extract statistical metrics from a statsmodels regression result object.
    
    Args:
        result: A statsmodels regression result object (e.g., GLMResults, OLSResults).
        feature_names: List of feature names corresponding to coefficients.
    
    Returns:
        Dictionary containing coefficients, standard errors, z-statistics, and p-values.
    """
    try:
        coefficients = result.params.values if hasattr(result.params, 'values') else result.params
        std_errors = result.bse.values if hasattr(result.bse, 'values') else result.bse
        
        if len(coefficients) != len(feature_names):
            logger.warning(
                f"Mismatch between feature names ({len(feature_names)}) "
                f"and coefficients ({len(coefficients)}). Using index-based mapping."
            )
            # Fallback: use index-based mapping if names don't match
            feature_names = [f"var_{i}" for i in range(len(coefficients))]
        
        metrics = {
            "coefficients": {},
            "standard_errors": {},
            "z_statistics": {},
            "p_values": {}
        }
        
        for i, (feature, coef, se) in enumerate(zip(feature_names, coefficients, std_errors)):
            z_stat, p_val = calculate_wald_z_test(coef, se)
            
            metrics["coefficients"][feature] = float(coef)
            metrics["standard_errors"][feature] = float(se)
            metrics["z_statistics"][feature] = float(z_stat)
            metrics["p_values"][feature] = float(p_val)
        
        # Extract model-level metrics if available
        if hasattr(result, 'rsquared'):
            metrics["r_squared"] = float(result.rsquared)
        
        if hasattr(result, 'aic'):
            metrics["aic"] = float(result.aic)
        
        if hasattr(result, 'bic'):
            metrics["bic"] = float(result.bic)
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error extracting metrics from statsmodels result: {e}")
        raise

def calculate_feature_significance(
    p_values: Dict[str, float],
    alpha: float = 0.05,
    apply_fdr: bool = True
) -> Dict[str, Dict[str, Any]]:
    """
    Calculate feature significance with optional FDR correction.
    
    Args:
        p_values: Dictionary mapping feature names to p-values.
        alpha: Significance level.
        apply_fdr: Whether to apply Benjamini-Hochberg FDR correction.
    
    Returns:
        Dictionary with significance information for each feature.
    """
    features = list(p_values.keys())
    raw_p_values = [p_values[f] for f in features]
    
    if apply_fdr and len(raw_p_values) > 1:
        adjusted_p_values, rejection_mask = apply_benjamini_hochberg_fdr(raw_p_values, alpha)
    else:
        adjusted_p_values = raw_p_values
        rejection_mask = [p <= alpha for p in raw_p_values]
    
    significance_results = {}
    for i, feature in enumerate(features):
        significance_results[feature] = {
            "raw_p_value": raw_p_values[i],
            "adjusted_p_value": adjusted_p_values[i],
            "is_significant": rejection_mask[i],
            "significant_at_alpha": rejection_mask[i]
        }
    
    return significance_results