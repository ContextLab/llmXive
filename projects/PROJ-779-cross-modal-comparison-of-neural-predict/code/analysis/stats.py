"""
Statistical analysis functions for cross-modal comparison of neural prediction error signals.

This module implements:
- Mixed-Effects Permutation Test for source strength modality comparison
- Independent samples t-test for source strength comparison
- TOST (Two One-Sided Tests) for equivalence testing
- Benjamini-Hochberg correction for multiple comparisons

All statistical tests are designed to work with CPU-only environments and limited RAM.
"""

import numpy as np
from typing import Dict, Any, Optional, Tuple, List
import logging

from code.utils.logger import get_logger

logger = get_logger(__name__)

def mixed_effects_permutation_test(
    group1: np.ndarray,
    group2: np.ndarray,
    n_permutations: int = 1000,
    random_state: Optional[int] = None,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform a mixed-effects permutation test for comparing source strength between two modalities.
    
    This test preserves the subject-level structure while permuting group labels,
    making it suitable for within-subject designs common in EEG/MEG studies.
    
    Parameters
    ----------
    group1 : np.ndarray
        Source strength data for first modality (subjects x sources)
    group2 : np.ndarray
        Source strength data for second modality (subjects x sources)
    n_permutations : int
        Number of permutations to perform (default: 1000)
    random_state : int, optional
        Random seed for reproducibility
    alpha : float
        Significance level for p-value calculation (default: 0.05)
    
    Returns
    -------
    dict
        Dictionary containing:
        - 'observed_t': The t-statistic for the observed data
        - 'p_value': The permutation-based p-value
        - 'permuted_t_distribution': Array of t-statistics from permuted data
        - 'n_permutations': Number of permutations performed
    
    Raises
    ------
    ValueError
        If input arrays have incompatible shapes or contain invalid values
    """
    if random_state is not None:
        np.random.seed(random_state)
    
    # Validate inputs
    if group1.shape != group2.shape:
        raise ValueError(
            f"Group shapes must match. Got {group1.shape} and {group2.shape}"
        )
    
    if group1.shape[0] < 2:
        raise ValueError(
            f"Insufficient subjects for permutation test. Got {group1.shape[0]}, need at least 2"
        )
    
    if np.any(np.isnan(group1)) or np.any(np.isnan(group2)):
        raise ValueError("Input arrays contain NaN values. Please handle missing data before testing.")
    
    n_subjects, n_sources = group1.shape
    
    # Calculate observed t-statistic (paired t-test for within-subject design)
    diff = group1 - group2
    observed_t = _calculate_t_statistic(diff)
    
    logger.info(f"Observed t-statistic: {observed_t:.4f}")
    
    # Generate permutation distribution
    permuted_t_distribution = np.zeros(n_permutations)
    
    for i in range(n_permutations):
        # Randomly flip signs for each subject (preserves within-subject structure)
        sign_flip = np.random.choice([-1, 1], size=n_subjects)
        permuted_diff = diff * sign_flip[:, np.newaxis]
        permuted_t = _calculate_t_statistic(permuted_diff)
        permuted_t_distribution[i] = permuted_t
    
    # Calculate p-value (two-tailed)
    # Count how many permuted statistics are as extreme or more extreme than observed
    extreme_count = np.sum(np.abs(permuted_t_distribution) >= np.abs(observed_t))
    p_value = (extreme_count + 1) / (n_permutations + 1)  # Add 1 for observed statistic
    
    logger.info(f"Permutation test completed. P-value: {p_value:.4f} ({n_permutations} permutations)")
    
    return {
        'observed_t': float(observed_t),
        'p_value': float(p_value),
        'permuted_t_distribution': permuted_t_distribution,
        'n_permutations': n_permutations
    }

def _calculate_t_statistic(diff: np.ndarray) -> float:
    """
    Calculate t-statistic for difference data.
    
    Parameters
    ----------
    diff : np.ndarray
        Difference data (subjects x sources)
    
    Returns
    -------
    float
        Mean t-statistic across all sources
    """
    # Calculate t-statistic for each source
    n_subjects = diff.shape[0]
    mean_diff = np.mean(diff, axis=0)
    std_diff = np.std(diff, axis=0, ddof=1)
    
    # Avoid division by zero
    std_diff[std_diff == 0] = 1e-10
    
    t_values = mean_diff / (std_diff / np.sqrt(n_subjects))
    
    # Return mean t-statistic across sources (for global test)
    return float(np.mean(t_values))

def independent_samples_ttest(
    group1: np.ndarray,
    group2: np.ndarray,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform independent samples t-test for source strength comparison.
    
    Note: This is a simplified version that treats all subjects as independent,
    which may not be appropriate for within-subject designs. Use with caution.
    
    Parameters
    ----------
    group1 : np.ndarray
        Source strength data for first modality
    group2 : np.ndarray
        Source strength data for second modality
    alpha : float
        Significance level (default: 0.05)
    
    Returns
    -------
    dict
        Dictionary containing:
        - 't_statistic': The t-statistic
        - 'p_value': The p-value
        - 'degrees_of_freedom': Degrees of freedom
        - 'significant': Boolean indicating if result is significant
    """
    # Flatten data for independent samples test
    flat1 = group1.flatten()
    flat2 = group2.flatten()
    
    n1, n2 = len(flat1), len(flat2)
    mean1, mean2 = np.mean(flat1), np.mean(flat2)
    var1, var2 = np.var(flat1, ddof=1), np.var(flat2, ddof=1)
    
    # Pooled standard error
    se = np.sqrt(var1/n1 + var2/n2)
    if se == 0:
        se = 1e-10
    
    t_stat = (mean1 - mean2) / se
    
    # Degrees of freedom (Welch-Satterthwaite equation)
    df = (var1/n1 + var2/n2)**2 / (
        (var1/n1)**2/(n1-1) + (var2/n2)**2/(n2-1)
    )
    
    # Two-tailed p-value approximation (using normal distribution for large samples)
    # For exact p-value, would need scipy.stats.t.sf
    p_value = 2 * (1 - _norm_cdf(abs(t_stat)))
    
    significant = p_value < alpha
    
    logger.info(f"Independent t-test: t={t_stat:.4f}, p={p_value:.4f}, df={df:.2f}")
    
    return {
        't_statistic': float(t_stat),
        'p_value': float(p_value),
        'degrees_of_freedom': float(df),
        'significant': significant
    }

def _norm_cdf(x: float) -> float:
    """
    Approximate standard normal CDF using error function approximation.
    
    Parameters
    ----------
    x : float
        Input value
    
    Returns
    -------
    float
        Cumulative probability
    """
    # Approximation of standard normal CDF
    t = 1.0 / (1.0 + 0.2316419 * abs(x))
    d = 0.3989423 * np.exp(-x * x / 2.0)
    p = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))))
    if x > 0:
        p = 1.0 - p
    return p

def tost_equivalence_test(
    group1: np.ndarray,
    group2: np.ndarray,
    equivalence_margin: float = 0.5,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform Two One-Sided Tests (TOST) for equivalence testing.
    
    Tests whether the difference between groups is within a specified equivalence margin.
    
    Parameters
    ----------
    group1 : np.ndarray
        Source strength data for first modality
    group2 : np.ndarray
        Source strength data for second modality
    equivalence_margin : float
        Maximum acceptable difference for equivalence (default: 0.5)
    alpha : float
        Significance level (default: 0.05)
    
    Returns
    -------
    dict
        Dictionary containing:
        - 't_lower': T-statistic for lower bound test
        - 't_upper': T-statistic for upper bound test
        - 'p_lower': P-value for lower bound test
        - 'p_upper': P-value for upper bound test
        - 'equivalent': Boolean indicating if groups are equivalent
        - 'mean_difference': Observed mean difference
    """
    # Flatten data
    flat1 = group1.flatten()
    flat2 = group2.flatten()
    
    n1, n2 = len(flat1), len(flat2)
    mean_diff = np.mean(flat1) - np.mean(flat2)
    pooled_std = np.sqrt(
        (np.var(flat1, ddof=1) + np.var(flat2, ddof=1)) / 2
    )
    
    if pooled_std == 0:
        pooled_std = 1e-10
    
    # Standard error of difference
    se = pooled_std * np.sqrt(1/n1 + 1/n2)
    
    # Two one-sided tests
    t_lower = (mean_diff - (-equivalence_margin)) / se
    t_upper = (mean_diff - equivalence_margin) / se
    
    # P-values (one-tailed)
    p_lower = 1 - _norm_cdf(t_lower)
    p_upper = 1 - _norm_cdf(-t_upper)
    
    # Equivalence requires both tests to be significant
    equivalent = (p_lower < alpha) and (p_upper < alpha)
    
    logger.info(
        f"TOST: mean_diff={mean_diff:.4f}, margin={equivalence_margin}, "
        f"p_lower={p_lower:.4f}, p_upper={p_upper:.4f}, equivalent={equivalent}"
    )
    
    return {
        't_lower': float(t_lower),
        't_upper': float(t_upper),
        'p_lower': float(p_lower),
        'p_upper': float(p_upper),
        'equivalent': equivalent,
        'mean_difference': float(mean_diff),
        'equivalence_margin': float(equivalence_margin)
    }

def benjamini_hochberg_correction(
    p_values: List[float],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Apply Benjamini-Hochberg correction for multiple comparisons.
    
    Controls the false discovery rate (FDR) across multiple hypothesis tests.
    
    Parameters
    ----------
    p_values : List[float]
        List of p-values to correct
    alpha : float
        Target FDR level (default: 0.05)
    
    Returns
    -------
    dict
        Dictionary containing:
        - 'corrected_p_values': Benjamini-Hochberg adjusted p-values
        - 'significant': Boolean array indicating which tests are significant
        - 'n_significant': Number of significant tests after correction
    """
    if not p_values:
        return {
            'corrected_p_values': [],
            'significant': [],
            'n_significant': 0
        }
    
    n_tests = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p_values = np.array(p_values)[sorted_indices]
    
    # Calculate BH critical values
    critical_values = (np.arange(1, n_tests + 1) / n_tests) * alpha
    
    # Find largest k such that p_(k) <= critical_k
    significant_mask = sorted_p_values <= critical_values
    if not np.any(significant_mask):
        corrected_p_values = np.ones(n_tests)
        significant = np.zeros(n_tests, dtype=bool)
    else:
        k = np.max(np.where(significant_mask)[0])
        # Adjust p-values
        corrected_p_values = np.minimum.accumulate(
            (sorted_p_values * n_tests) / (np.arange(1, n_tests + 1))
        )
        corrected_p_values = np.minimum(corrected_p_values, 1.0)
        
        # Reorder to original indices
        final_corrected = np.zeros(n_tests)
        final_corrected[sorted_indices] = corrected_p_values
        
        significant = final_corrected < alpha
        corrected_p_values = final_corrected
    
    n_significant = int(np.sum(significant))
    
    logger.info(
        f"BH correction: {n_significant}/{n_tests} tests significant "
        f"(FDR={alpha})"
    )
    
    return {
        'corrected_p_values': corrected_p_values.tolist(),
        'significant': significant.tolist(),
        'n_significant': n_significant
    }