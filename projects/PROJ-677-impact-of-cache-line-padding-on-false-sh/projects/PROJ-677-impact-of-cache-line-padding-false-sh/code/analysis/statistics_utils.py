"""
Statistical utilities for analyzing benchmark results.

This module provides functions for calculating effect sizes (Cohen's d)
and performing two-sample t-tests to compare counter performance between
packed and padded configurations.
"""

import math
from typing import List, Tuple


def calculate_mean(data: List[float]) -> float:
    """Calculate the arithmetic mean of a list of numbers."""
    if not data:
        raise ValueError("Cannot calculate mean of empty list")
    return sum(data) / len(data)


def calculate_variance(data: List[float], ddof: int = 1) -> float:
    """
    Calculate the sample variance of a list of numbers.
    
    Args:
        data: List of numeric values
        ddof: Delta degrees of freedom (1 for sample variance, 0 for population)
    
    Returns:
        Sample variance
    """
    if len(data) <= ddof:
        raise ValueError(f"Need more than {ddof} data points to calculate variance")
    
    mean = calculate_mean(data)
    squared_diffs = [(x - mean) ** 2 for x in data]
    return sum(squared_diffs) / (len(data) - ddof)


def cohens_d(group1: List[float], group2: List[float]) -> float:
    """
    Calculate Cohen's d effect size between two groups.
    
    Cohen's d is a measure of effect size, indicating the standardized
    difference between two means.
    
    Formula: d = (mean1 - mean2) / pooled_std
    where pooled_std = sqrt((var1 + var2) / 2)
    
    Args:
        group1: List of values from the first group
        group2: List of values from the second group
    
    Returns:
        Cohen's d value
    
    Raises:
        ValueError: If input lists are empty or have insufficient data
        ZeroDivisionError: If pooled standard deviation is zero
    """
    if not group1 or not group2:
        raise ValueError("Input lists cannot be empty")
    
    mean1 = calculate_mean(group1)
    mean2 = calculate_mean(group2)
    
    var1 = calculate_variance(group1)
    var2 = calculate_variance(group2)
    
    # Pooled standard deviation (assuming equal sample sizes or using simple average)
    pooled_var = (var1 + var2) / 2
    
    if pooled_var == 0:
        raise ZeroDivisionError("Pooled variance is zero, cannot calculate Cohen's d")
    
    pooled_std = math.sqrt(pooled_var)
    
    return (mean1 - mean2) / pooled_std


def two_sample_ttest(group1: List[float], group2: List[float]) -> Tuple[float, float]:
    """
    Perform an independent two-sample t-test.
    
    Uses Welch's t-test (unequal variance t-test) which does not assume
    equal variances between the two groups.
    
    Args:
        group1: List of values from the first group
        group2: List of values from the second group
    
    Returns:
        Tuple of (t_statistic, p_value)
    
    Raises:
        ValueError: If input lists are empty or have insufficient data
    """
    if not group1 or not group2:
        raise ValueError("Input lists cannot be empty")
    
    n1 = len(group1)
    n2 = len(group2)
    
    if n1 < 2 or n2 < 2:
        raise ValueError("Each group must have at least 2 samples for t-test")
    
    mean1 = calculate_mean(group1)
    mean2 = calculate_mean(group2)
    var1 = calculate_variance(group1)
    var2 = calculate_variance(group2)
    
    # Welch's t-test
    se = math.sqrt(var1 / n1 + var2 / n2)
    
    if se == 0:
        raise ZeroDivisionError("Standard error is zero, cannot calculate t-statistic")
    
    t_stat = (mean1 - mean2) / se
    
    # Degrees of freedom (Welch-Satterthwaite equation)
    num = (var1 / n1 + var2 / n2) ** 2
    denom = ((var1 / n1) ** 2 / (n1 - 1)) + ((var2 / n2) ** 2 / (n2 - 1))
    df = num / denom
    
    # Calculate p-value using t-distribution CDF approximation
    # Using a simple approximation for the two-tailed p-value
    p_value = _t_distribution_p_value(t_stat, df)
    
    return t_stat, p_value


def _t_distribution_p_value(t_stat: float, df: float) -> float:
    """
    Calculate the two-tailed p-value for a t-statistic.
    
    Uses a numerical approximation of the Student's t-distribution CDF.
    
    Args:
        t_stat: The t-statistic value
        df: Degrees of freedom
    
    Returns:
        Two-tailed p-value
    """
    # For large df, t-distribution approaches normal distribution
    # Use a simple approximation based on the error function
    # This is an approximation suitable for statistical testing
    
    # Absolute value for two-tailed test
    t_abs = abs(t_stat)
    
    # Approximation using the regularized incomplete beta function
    # This is a simplified version suitable for most practical cases
    x = df / (df + t_abs ** 2)
    
    # Regularized incomplete beta function approximation
    # Using a simple series expansion for I_x(a, b)
    a = df / 2
    b = 0.5
    
    # Numerical integration approximation
    # For practical purposes, we use a standard library if available
    # or a simple approximation
    
    try:
        from scipy import stats
        p_value = 2 * (1 - stats.t.cdf(t_abs, df))
    except ImportError:
        # Fallback to a simple approximation when scipy is not available
        # This is less accurate but functional
        if df > 30:
            # Approximate with normal distribution
            from math import erf, sqrt
            z = t_abs
            p_value = 2 * (1 - (0.5 * (1 + erf(z / sqrt(2)))))
        else:
            # Simple heuristic for small df
            # This is a rough approximation
            p_value = 2 * (1 / (1 + t_abs * sqrt(df / (df + t_abs ** 2))))
    
    # Ensure p-value is in valid range
    return max(0.0, min(1.0, p_value))


def benjamini_hochberg(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values
    
    Returns:
        List of adjusted p-values
    """
    if not p_values:
        return []
    
    n = len(p_values)
    # Create list of (original_index, p_value)
    indexed_pvals = list(enumerate(p_values))
    # Sort by p-value
    sorted_pvals = sorted(indexed_pvals, key=lambda x: x[1])
    
    adjusted = [0.0] * n
    last_idx = sorted_pvals[-1][0]
    adjusted[last_idx] = sorted_pvals[-1][1]
    
    # Work backwards
    for i in range(n - 2, -1, -1):
        orig_idx, p_val = sorted_pvals[i]
        # BH formula: p * n / rank
        # rank is i + 1 (1-based)
        adjusted_val = p_val * n / (i + 1)
        # Ensure monotonicity
        adjusted_val = min(adjusted_val, adjusted[sorted_pvals[i + 1][0]])
        # Clamp to [0, 1]
        adjusted_val = max(0.0, min(1.0, adjusted_val))
        adjusted[orig_idx] = adjusted_val
    
    return adjusted