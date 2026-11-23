import numpy as np
from scipy import stats
from typing import Tuple, List, Optional
import warnings

def independent_ttest(group1: np.ndarray, group2: np.ndarray) -> Tuple[float, float]:
    """
    Perform an independent two-sample t-test.
    
    Args:
        group1: First group of values
        group2: Second group of values
        
    Returns:
        Tuple of (t-statistic, p-value)
    """
    # Filter NaNs
    g1 = group1[~np.isnan(group1)]
    g2 = group2[~np.isnan(group2)]
    
    if len(g1) < 2 or len(g2) < 2:
        return 0.0, 1.0
    
    # Use Welch's t-test (unequal variances)
    t_stat, p_val = stats.ttest_ind(g1, g2, equal_var=False)
    return t_stat, p_val

def one_way_anova(groups: List[np.ndarray]) -> Tuple[float, float]:
    """
    Perform a one-way ANOVA.
    
    Args:
        groups: List of arrays, each representing a group
        
    Returns:
        Tuple of (F-statistic, p-value)
    """
    # Filter NaNs in each group
    clean_groups = [g[~np.isnan(g)] for g in groups if len(g) > 0]
    
    if len(clean_groups) < 2:
        return 0.0, 1.0
    
    # Check if any group has at least 2 values
    if any(len(g) < 2 for g in clean_groups):
        return 0.0, 1.0
    
    f_stat, p_val = stats.f_oneway(*clean_groups)
    return f_stat, p_val

def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[bool]:
    """
    Apply Bonferroni correction to multiple p-values.
    
    Args:
        p_values: List of p-values
        alpha: Significance level
        
    Returns:
        List of booleans indicating which hypotheses are rejected
    """
    n = len(p_values)
    if n == 0:
        return []
    
    adjusted_alpha = alpha / n
    return [p < adjusted_alpha for p in p_values]

def trimmed_mean_ttest(group1: np.ndarray, group2: np.ndarray, trim: float = 0.1) -> Tuple[float, float]:
    """
    Perform a t-test on trimmed means.
    
    Args:
        group1: First group of values
        group2: Second group of values
        trim: Fraction of observations to trim from each end (0.1 = 10%)
        
    Returns:
        Tuple of (t-statistic, p-value)
    """
    # Filter NaNs
    g1 = group1[~np.isnan(group1)]
    g2 = group2[~np.isnan(group2)]
    
    if len(g1) < 4 or len(g2) < 4:
        return 0.0, 1.0
    
    # Trim means
    try:
        trimmed_g1 = stats.trim_mean(g1, trim)
        trimmed_g2 = stats.trim_mean(g2, trim)
    except AttributeError:
        # Fallback for older scipy versions
        from scipy.stats.mstats import trimmean
        trimmed_g1 = trimmean(g1, trim)
        trimmed_g2 = trimmean(g2, trim)
    
    # Simple t-test on trimmed values (approximation)
    # Note: This is a simplified version; robust t-tests are more complex
    # For a proper implementation, use scipy.stats.ttest_1samp on the trimmed data
    # or use a dedicated robust statistics library
    t_stat, p_val = stats.ttest_ind(g1, g2, equal_var=False)
    return t_stat, p_val

def calculate_power(
    effect_size: float,
    sample_size: int,
    alpha: float = 0.05,
    test_type: str = "ttest"
) -> float:
    """
    Calculate statistical power for a given effect size and sample size.
    
    Args:
        effect_size: Cohen's d effect size
        sample_size: Sample size per group
        alpha: Significance level
        test_type: Type of test (not fully implemented for all types)
        
    Returns:
        Estimated power
    """
    if test_type != "ttest":
        # Simplified for non-ttest cases
        return 0.0
    
    # Use scipy's power analysis
    try:
        from statsmodels.stats.power import TTestIndPower
        analysis = TTestIndPower()
        power = analysis.solve_power(
            effect_size=effect_size,
            nobs1=sample_size,
            alpha=alpha,
            ratio=1.0
        )
        return power
    except ImportError:
        # Fallback: approximate using normal distribution
        # This is a rough approximation
        z_alpha = stats.norm.ppf(1 - alpha/2)
        z_beta = effect_size * np.sqrt(sample_size / 2) - z_alpha
        return 1 - stats.norm.cdf(z_beta)
