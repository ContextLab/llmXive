"""
Statistical utilities for permutation testing and FDR correction.
"""
import numpy as np
from statsmodels.stats.multitest import fdrcorrection as fdr_bh
import logging

logger = logging.getLogger(__name__)

def apply_fdr_correction(p_values, alpha=0.05):
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.
    
    Args:
        p_values: List or array of p-values.
        alpha: Significance level (default 0.05).
        
    Returns:
        Tuple (reject, p_corrected) where reject is a boolean array
        indicating which hypotheses are rejected.
    """
    p_values = np.array(p_values)
    if len(p_values) == 0:
        return np.array([]), np.array([])
    
    reject, p_corrected = fdr_bh(p_values, alpha=alpha, is_sorted=False, multipletests="fdr_bh")
    logger.info(f"FDR Correction: {np.sum(reject)} significant findings at alpha={alpha}")
    return reject, p_corrected

def permutation_test(observed_diff, null_distribution, n_permutations=1000, seed=None):
    """
    Perform a permutation test to assess significance.
    
    Args:
        observed_diff: The observed test statistic (e.g., difference in means).
        null_distribution: An array of null statistics generated via permutation.
        n_permutations: Number of permutations used to generate the null distribution.
        seed: Random seed for reproducibility.
        
    Returns:
        p_value: Two-tailed p-value.
    """
    if seed is not None:
        np.random.seed(seed)
        
    null_distribution = np.array(null_distribution)
    
    # Calculate p-value as proportion of null stats >= observed (absolute)
    # Two-tailed test logic
    abs_observed = np.abs(observed_diff)
    abs_null = np.abs(null_distribution)
    
    p_value = np.mean(abs_null >= abs_observed)
    
    logger.debug(f"Permutation Test: Observed={observed_diff:.4f}, P-value={p_value:.4f}")
    return p_value
