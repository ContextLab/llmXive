"""
Statistical helper functions for robustness analysis.

Provides implementations for:
- Standard t-tests (independent samples)
- One-way ANOVA
- Bonferroni correction for multiple comparisons
- Robust t-test using trimmed means (via scipy)
"""

import numpy as np
from scipy import stats
from typing import Tuple, List, Optional
import warnings

# Suppress specific scipy warnings about convergence if necessary
warnings.filterwarnings('ignore', category=stats.SpecificWarning)


def independent_ttest(group1: np.ndarray, group2: np.ndarray, equal_var: bool = True) -> Tuple[float, float]:
    """
    Perform an independent two-sample t-test.

    Parameters
    ----------
    group1 : np.ndarray
        First sample data.
    group2 : np.ndarray
        Second sample data.
    equal_var : bool, default=True
        If True, perform a standard independent 2 sample t-test that assumes
        that the two populations have equal variances (Student's t-test).
        If False, perform Welch's t-test, which does not assume equal variances.

    Returns
    -------
    tuple (statistic, p-value)
        The t-statistic and the two-sided p-value.
    """
    # Handle empty or single-element arrays gracefully
    if len(group1) < 2 or len(group2) < 2:
        return 0.0, 1.0

    try:
        t_stat, p_val = stats.ttest_ind(group1, group2, equal_var=equal_var)
        return float(t_stat), float(p_val)
    except Exception:
        # Fallback for edge cases (e.g., constant variance in one group causing division by zero)
        return 0.0, 1.0


def one_way_anova(groups: List[np.ndarray]) -> Tuple[float, float]:
    """
    Perform a one-way ANOVA.

    Parameters
    ----------
    groups : list of np.ndarray
        List of arrays, each representing a group's data.

    Returns
    -------
    tuple (statistic, p-value)
        The F-statistic and the p-value.
    """
    # Filter out empty groups
    valid_groups = [g for g in groups if len(g) >= 2]
    
    if len(valid_groups) < 2:
        return 0.0, 1.0

    try:
        f_stat, p_val = stats.f_oneway(*valid_groups)
        return float(f_stat), float(p_val)
    except Exception:
        return 0.0, 1.0


def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], List[bool]]:
    """
    Apply Bonferroni correction for multiple comparisons.

    Parameters
    ----------
    p_values : list of float
        List of raw p-values from multiple tests.
    alpha : float, default=0.05
        Significance level for the family-wise error rate.

    Returns
    -------
    tuple (adjusted_p_values, significant_flags)
        - adjusted_p_values: List of Bonferroni-corrected p-values.
        - significant_flags: List of booleans indicating if the test is significant after correction.
    """
    if not p_values:
        return [], []

    n_tests = len(p_values)
    adjusted_p_values = []
    significant_flags = []

    for p in p_values:
        # Bonferroni adjustment: p_adj = min(p * n, 1.0)
        p_adj = min(p * n_tests, 1.0)
        adjusted_p_values.append(p_adj)
        significant_flags.append(p_adj < alpha)

    return adjusted_p_values, significant_flags


def trimmed_mean_ttest(group1: np.ndarray, group2: np.ndarray, trim_fraction: float = 0.1) -> Tuple[float, float]:
    """
    Perform a t-test on trimmed means.

    This is a robust alternative to the standard t-test that removes a fraction
    of the smallest and largest values from each group before testing.

    Parameters
    ----------
    group1 : np.ndarray
        First sample data.
    group2 : np.ndarray
        Second sample data.
    trim_fraction : float, default=0.1
        Fraction of observations to trim from each end of the distribution (0.0 to 0.5).

    Returns
    -------
    tuple (statistic, p-value)
        The t-statistic and the two-sided p-value based on trimmed means.
    """
    if len(group1) < 2 or len(group2) < 2:
        return 0.0, 1.0

    try:
        # scipy.stats.ttest_ind_froms requires means and standard errors, 
        # but we can use the generic ttest_ind on the trimmed data directly.
        # However, for a true trimmed mean test (Yuen's test), scipy doesn't have a direct built-in 
        # in older versions, but we can approximate by trimming the data and running ttest_ind.
        # Note: This changes the variance estimate slightly compared to Yuen's exact method,
        # but is a standard robust approach in this context.
        
        # Trim the data
        t1 = stats.trim_mean(group1, trim_fraction)
        t2 = stats.trim_mean(group2, trim_fraction)
        
        # We need the trimmed data to calculate the correct variance for the test statistic.
        # scipy.stats.ttest_ind can run on the trimmed arrays directly.
        g1_trimmed = stats.trimboth(group1, trim_fraction)
        g2_trimmed = stats.trimboth(group2, trim_fraction)
        
        if len(g1_trimmed) < 2 or len(g2_trimmed) < 2:
            return 0.0, 1.0

        t_stat, p_val = stats.ttest_ind(g1_trimmed, g2_trimmed, equal_var=False) # Welch's is safer for trimmed
        return float(t_stat), float(p_val)
    except Exception:
        return 0.0, 1.0


def calculate_power(t_stat: float, n1: int, n2: int, alpha: float = 0.05) -> float:
    """
    Estimate statistical power based on observed t-statistic and sample sizes.
    
    This is an approximation using the non-central t-distribution.
    
    Parameters
    ----------
    t_stat : float
        Observed t-statistic.
    n1, n2 : int
        Sample sizes of the two groups.
    alpha : float
        Significance level.
        
    Returns
    -------
    float
        Estimated power (probability of rejecting null when alternative is true).
    """
    if n1 < 2 or n2 < 2:
        return 0.0
        
    df = n1 + n2 - 2
    # Approximate non-centrality parameter (delta)
    # t = delta / sqrt(1/n1 + 1/n2)  => delta = t * sqrt(1/n1 + 1/n2)^-1
    # Actually, standard error is sqrt(s1^2/n1 + s2^2/n2). 
    # For power estimation from observed t, we treat the observed t as the non-centrality parameter scaled.
    # A common approximation: delta = t_stat * sqrt( (n1*n2)/(n1+n2) )
    delta = t_stat * np.sqrt((n1 * n2) / (n1 + n2))
    
    # Critical t value
    t_crit = stats.t.ppf(1 - alpha/2, df)
    
    # Power = P(T > t_crit | delta) + P(T < -t_crit | delta)
    # Using non-central t-distribution
    power = stats.nct.sf(t_crit, df, delta) + stats.nct.cdf(-t_crit, df, delta)
    
    return float(power)