import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from scipy import stats
import logging

logger = logging.getLogger(__name__)

def calculate_wald_z_statistic(coefficient: float, standard_error: float) -> float:
    """
    Calculate the Wald Z-statistic for a coefficient.
    
    Args:
        coefficient: The estimated coefficient value.
        standard_error: The standard error of the coefficient.
        
    Returns:
        The Z-statistic.
        
    Raises:
        ValueError: If standard_error is zero or negative.
    """
    if standard_error <= 0:
        raise ValueError("Standard error must be positive.")
    return coefficient / standard_error

def calculate_p_value_z_test(z_statistic: float, two_tailed: bool = True) -> float:
    """
    Calculate the p-value from a Z-statistic using the standard normal distribution.
    
    Args:
        z_statistic: The calculated Z-statistic.
        two_tailed: If True, returns two-tailed p-value; otherwise one-tailed.
        
    Returns:
        The p-value.
    """
    if two_tailed:
        return 2 * (1 - stats.norm.cdf(abs(z_statistic)))
    else:
        if z_statistic > 0:
            return 1 - stats.norm.cdf(z_statistic)
        else:
            return stats.norm.cdf(z_statistic)

def calculate_f_statistic(r_squared: float, n: int, p: int) -> float:
    """
    Calculate the F-statistic given R-squared, sample size, and number of predictors.
    
    Formula: F = (R^2 / p) / ((1 - R^2) / (n - p - 1))
    
    Args:
        r_squared: The R-squared value of the model.
        n: The number of observations (sample size).
        p: The number of predictors (excluding intercept).
        
    Returns:
        The F-statistic.
        
    Raises:
        ValueError: If inputs are invalid.
    """
    if n <= p + 1:
        raise ValueError("Sample size n must be greater than p + 1.")
    if r_squared >= 1.0 or r_squared < 0:
        # Handle edge case where R^2 is exactly 1 (perfect fit)
        if r_squared == 1.0:
            return float('inf')
        raise ValueError("R-squared must be between 0 and 1.")
        
    numerator = r_squared / p
    denominator = (1 - r_squared) / (n - p - 1)
    return numerator / denominator

def calculate_f_statistic_from_sums(ssr: float, sse: float, p: int, n: int) -> float:
    """
    Calculate the F-statistic from Sum of Squares.
    
    Formula: F = (SSR / p) / (SSE / (n - p - 1))
    
    Args:
        ssr: Sum of Squares due to Regression.
        sse: Sum of Squares due to Error.
        p: Number of predictors.
        n: Number of observations.
        
    Returns:
        The F-statistic.
    """
    if sse <= 0:
        # If SSE is 0, we have a perfect fit
        return float('inf')
    if n <= p + 1:
        raise ValueError("Sample size n must be greater than p + 1.")
        
    return (ssr / p) / (sse / (n - p - 1))

def apply_benjamini_hochberg_fdr(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], List[bool]]:
    """
    Apply the Benjamini-Hochberg procedure to control the False Discovery Rate (FDR).
    
    This function takes a list of raw p-values and returns adjusted p-values and a 
    boolean list indicating which hypotheses are rejected (significant) at the given 
    significance level alpha.
    
    Algorithm:
    1. Sort p-values in ascending order.
    2. Calculate the BH critical value for each: (i / m) * alpha, where i is rank (1-based) and m is total count.
    3. Find the largest k such that p_(k) <= (k / m) * alpha.
    4. Reject all hypotheses with p-values <= p_(k).
    
    Args:
        p_values: A list of raw p-values.
        alpha: The desired FDR level (significance threshold). Default 0.05.
        
    Returns:
        A tuple containing:
            - adjusted_p_values: List of adjusted p-values corresponding to the input order.
            - is_significant: List of booleans indicating if the hypothesis is rejected.
            
    Raises:
        ValueError: If p_values is empty or contains invalid values.
    """
    if not p_values:
        return [], []
        
    if any(p < 0 or p > 1 for p in p_values):
        raise ValueError("All p-values must be between 0 and 1.")
        
    m = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p_values = [p_values[i] for i in sorted_indices]
    
    # Calculate BH critical values and find the largest k
    # We need to find the largest k such that p_(k) <= (k/m) * alpha
    # Note: k is 1-based index in the sorted list
    
    reject_indices = []
    for i in range(m):
        k = i + 1  # 1-based rank
        critical_value = (k / m) * alpha
        if sorted_p_values[i] <= critical_value:
            reject_indices.append(i)
    
    if not reject_indices:
        # No rejections
        adjusted_p_values = [1.0] * m
        is_significant = [False] * m
    else:
        # The largest k found
        k_max = max(reject_indices) + 1
        
        # Calculate adjusted p-values
        # adj_p_i = min(1, min_{j >= i} (m/j * p_j))
        # Implementation:
        # 1. Compute raw adjusted values: p_i * m / i (where i is 1-based rank)
        # 2. Ensure monotonicity by taking cumulative minimum from the end
        
        adjusted_sorted = []
        for i, p in enumerate(sorted_p_values):
            rank = i + 1
            adj = p * m / rank
            adjusted_sorted.append(adj)
        
        # Enforce monotonicity: adjusted p-values must be non-decreasing with rank
        # We iterate backwards and ensure each value is <= the next one
        for i in range(m - 2, -1, -1):
            if adjusted_sorted[i] > adjusted_sorted[i + 1]:
                adjusted_sorted[i] = adjusted_sorted[i + 1]
        
        # Cap at 1.0
        adjusted_sorted = [min(1.0, x) for x in adjusted_sorted]
        
        # Map back to original order
        adjusted_p_values = [0.0] * m
        for idx, adj_val in zip(sorted_indices, adjusted_sorted):
            adjusted_p_values[idx] = adj_val
        
        # Determine significance based on the original BH step-up procedure
        # Reject if p_i <= (rank_i / m) * alpha
        is_significant = [False] * m
        for i, p in enumerate(p_values):
            rank = np.where(sorted_indices == i)[0][0] + 1
            if p <= (rank / m) * alpha:
                is_significant[i] = True
                
        # Actually, the standard BH procedure for significance is:
        # Reject all hypotheses where p_(i) <= (i/m)*alpha for i=1..k_max
        # Let's re-calculate significance based on the k_max found
        threshold = (k_max / m) * alpha
        is_significant = [p <= threshold for p in p_values]

    return adjusted_p_values, is_significant

def calculate_metric_summary(
    coefficients: Dict[str, float],
    standard_errors: Dict[str, float],
    p_values: Dict[str, float],
    r_squared: float,
    n_obs: int,
    n_preds: int
) -> Dict[str, Dict[str, float]]:
    """
    Calculate a summary of metrics for a regression model.
    
    Args:
        coefficients: Dictionary mapping feature names to coefficients.
        standard_errors: Dictionary mapping feature names to standard errors.
        p_values: Dictionary mapping feature names to raw p-values.
        r_squared: The R-squared value of the model.
        n_obs: Number of observations.
        n_preds: Number of predictors.
        
    Returns:
        A dictionary containing:
            - 'coefficients': Original coefficients
            - 'z_statistics': Calculated Z-statistics
            - 'p_values': Original p-values
            - 'f_statistic': Calculated F-statistic
            - 'model_r_squared': R-squared value
    """
    z_stats = {}
    for name, coef in coefficients.items():
        se = standard_errors.get(name, 0.0)
        if se > 0:
            z_stats[name] = calculate_wald_z_statistic(coef, se)
        else:
            z_stats[name] = 0.0
    
    f_stat = calculate_f_statistic(r_squared, n_obs, n_preds)
    
    return {
        'coefficients': coefficients,
        'standard_errors': standard_errors,
        'z_statistics': z_stats,
        'p_values': p_values,
        'f_statistic': f_stat,
        'model_r_squared': r_squared
    }

def main():
    """
    Main entry point for testing metrics calculations.
    This function demonstrates the usage of the Benjamini-Hochberg FDR correction
    and other metric calculations.
    """
    # Example data for demonstration
    test_p_values = [0.001, 0.04, 0.03, 0.002, 0.15, 0.20, 0.01, 0.06]
    alpha = 0.05
    
    logger.info("Testing Benjamini-Hochberg FDR Correction")
    logger.info(f"Raw p-values: {test_p_values}")
    
    adjusted, significant = apply_benjamini_hochberg_fdr(test_p_values, alpha)
    
    logger.info(f"Adjusted p-values: {adjusted}")
    logger.info(f"Significant (at alpha={alpha}): {significant}")
    
    # Demonstrate F-statistic calculation
    r2 = 0.75
    n = 1000
    p = 10
    f_stat = calculate_f_statistic(r2, n, p)
    logger.info(f"F-statistic for R²={r2}, n={n}, p={p}: {f_stat:.4f}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()