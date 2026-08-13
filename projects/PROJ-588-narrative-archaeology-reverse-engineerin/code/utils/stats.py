"""
Statistical utilities for permutation testing and FDR correction.
"""
import numpy as np
from statsmodels.stats.multitest import fdrcorrection
import logging

logger = logging.getLogger(__name__)

def apply_fdr_correction(p_values, alpha=0.05):
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.

    Args:
        p_values (list): List of p-values.
        alpha (float): Significance level.

    Returns:
        tuple: (rejected (bool array), p_corrected (array), alpha_corrected (float))
    """
    if not p_values:
        return np.array([]), np.array([]), 0.0

    p_values = np.array(p_values)
    reject, p_corrected, _, _ = fdrcorrection(p_values, alpha=alpha, method='indep')
    logger.info(f"FDR Correction: {np.sum(reject)} of {len(p_values)} tests significant at q < {alpha}")
    return reject, p_corrected, alpha

def permutation_test(observed, null_distribution, n_permutations=1000):
    """
    Perform a simple permutation test.

    Args:
        observed (float): Observed statistic.
        null_distribution (array): Array of null statistics.
        n_permutations (int): Number of permutations (used to generate null if empty).

    Returns:
        float: p-value.
    """
    if len(null_distribution) == 0:
        raise ValueError("Null distribution cannot be empty.")

    # Two-tailed p-value
    p_val = np.mean(np.abs(null_distribution) >= np.abs(observed))
    logger.debug(f"Permutation test p-value: {p_val}")
    return p_val
