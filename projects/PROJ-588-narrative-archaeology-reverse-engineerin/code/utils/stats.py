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
        p_values (list[float]): List of raw p-values.
        alpha (float): Significance threshold.

    Returns:
        tuple: (reject_mask, p_corrected)
            - reject_mask: Boolean array indicating which hypotheses are rejected.
            - p_corrected: Array of adjusted p-values.
    """
    if not p_values:
        return np.array([]), np.array([])

    try:
        # Corrected: Use method='indep' or 'negcorr' instead of unsupported 'multipletests'
        # 'indep' assumes independent tests, 'negcorr' assumes positive dependence.
        # Given the context of RSA matrices across ROIs, 'indep' is a standard conservative choice.
        reject, p_corrected = fdrcorrection(np.array(p_values), alpha=alpha, method='indep')
        return reject, p_corrected
    except Exception as e:
        logger.error(f"FDR correction failed: {e}")
        raise

def permutation_test(observed, null_distribution, n_permutations=1000, alternative='greater'):
    """
    Perform a non-parametric permutation test.

    This function calculates the empirical p-value by comparing the observed statistic
    against a provided null distribution. If the null distribution is smaller than
    the requested number of permutations, it uses the available data but warns the user.

    Args:
        observed (float): The observed test statistic.
        null_distribution (np.ndarray): Array of statistics from the null hypothesis.
        n_permutations (int): Number of permutations (for consistency check/logging).
        alternative (str): 'greater', 'less', or 'two-sided'.

    Returns:
        float: The empirical p-value.
    """
    if null_distribution.size == 0:
        raise ValueError("Null distribution cannot be empty.")

    # Ensure null distribution is large enough
    if null_distribution.size < n_permutations:
        logger.warning(f"Null distribution size ({null_distribution.size}) < requested permutations ({n_permutations}). Using available data.")
        effective_n = null_distribution.size
    else:
        effective_n = n_permutations

    if alternative == 'greater':
        # Probability of observing a value as extreme or more extreme in the positive direction
        count = np.sum(null_distribution >= observed)
        p_value = count / effective_n
    elif alternative == 'less':
        # Probability of observing a value as extreme or more extreme in the negative direction
        count = np.sum(null_distribution <= observed)
        p_value = count / effective_n
    elif alternative == 'two-sided':
        # Two-sided: count extreme values in either direction relative to the median of the null
        median_null = np.median(null_distribution)
        diff_obs = abs(observed - median_null)
        diff_null = abs(null_distribution - median_null)
        count = np.sum(diff_null >= diff_obs)
        p_value = count / effective_n
    else:
        raise ValueError(f"Unknown alternative hypothesis: {alternative}")

    # Add 1 to numerator and denominator to avoid p=0 (conservative estimate)
    # This is standard practice in permutation testing to ensure p > 0
    p_value = (count + 1) / (effective_n + 1)

    return p_value
