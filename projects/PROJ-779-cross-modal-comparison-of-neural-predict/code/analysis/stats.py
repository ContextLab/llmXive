"""
Statistical analysis module for cross-modal comparison of neural prediction error signals.
Implements permutation tests, t-tests, equivalence tests, and multiple comparison corrections.
"""

import numpy as np
from typing import Dict, Any, Optional, Tuple, List
import logging
from scipy import stats
from code.utils.logger import get_logger
from code.config import get_config

logger = get_logger(__name__)


class StatsError(Exception):
    """Custom exception for statistical analysis errors."""
    pass


def mixed_effects_permutation_test(
    data_a: np.ndarray,
    data_b: np.ndarray,
    n_permutations: int = 5000,
    seed: Optional[int] = None,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform a mixed-effects permutation test for source strength modality comparison.

    Args:
        data_a: Source strength values for modality A (e.g., auditory).
        data_b: Source strength values for modality B (e.g., visual).
        n_permutations: Number of permutations to run.
        seed: Random seed for reproducibility.
        alpha: Significance level.

    Returns:
        Dictionary containing p-value, test statistic, and significance flag.
    """
    if seed is not None:
        np.random.seed(seed)

    if len(data_a) < 2 or len(data_b) < 2:
        raise StatsError("Both datasets must have at least 2 samples for permutation test.")

    # Observed statistic (difference in means)
    obs_stat = np.mean(data_a) - np.mean(data_b)

    # Combine data
    combined = np.concatenate([data_a, data_b])
    n_a = len(data_a)
    n_total = len(combined)

    # Permutation distribution
    perm_stats = np.zeros(n_permutations)
    for i in range(n_permutations):
        np.random.shuffle(combined)
        perm_a = combined[:n_a]
        perm_b = combined[n_a:]
        perm_stats[i] = np.mean(perm_a) - np.mean(perm_b)

    # Two-tailed p-value
    p_value = (np.sum(np.abs(perm_stats) >= np.abs(obs_stat)) + 1) / (n_permutations + 1)

    return {
        "test_statistic": float(obs_stat),
        "p_value": float(p_value),
        "n_permutations": n_permutations,
        "significant": bool(p_value < alpha),
        "alpha": alpha
    }


def independent_samples_ttest(
    data_a: np.ndarray,
    data_b: np.ndarray,
    equal_var: bool = True
) -> Dict[str, Any]:
    """
    Perform an independent samples t-test for source strength modality comparison.

    Args:
        data_a: Source strength values for modality A.
        data_b: Source strength values for modality B.
        equal_var: If True, perform standard t-test (assume equal variance).
                   If False, perform Welch's t-test.

    Returns:
        Dictionary containing t-statistic, p-value, and degrees of freedom.
    """
    if len(data_a) < 2 or len(data_b) < 2:
        raise StatsError("Both datasets must have at least 2 samples for t-test.")

    t_stat, p_value = stats.ttest_ind(data_a, data_b, equal_var=equal_var)

    return {
        "t_statistic": float(t_stat),
        "p_value": float(p_value),
        "degrees_of_freedom": float(stats.ttest_ind(data_a, data_b, equal_var=equal_var).df if equal_var else np.nan),
        "method": "independent_samples_ttest" if equal_var else "welch_ttest"
    }


def tost_equivalence_test(
    data_a: np.ndarray,
    data_b: np.ndarray,
    equivalence_margin: float = 0.5,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform Two One-Sided Tests (TOST) for equivalence of source strength.

    Args:
        data_a: Source strength values for modality A.
        data_b: Source strength values for modality B.
        equivalence_margin: The equivalence margin (delta).
        alpha: Significance level.

    Returns:
        Dictionary containing p-values for both one-sided tests and equivalence decision.
    """
    if len(data_a) < 2 or len(data_b) < 2:
        raise StatsError("Both datasets must have at least 2 samples for TOST.")

    mean_a = np.mean(data_a)
    mean_b = np.mean(data_b)
    std_a = np.std(data_a, ddof=1)
    std_b = np.std(data_b, ddof=1)
    n_a = len(data_a)
    n_b = len(data_b)

    pooled_se = np.sqrt((std_a**2 / n_a) + (std_b**2 / n_b))
    diff = mean_a - mean_b

    # Lower bound test: H0: diff <= -margin
    t_lower = (diff + equivalence_margin) / pooled_se
    p_lower = 1 - stats.t.cdf(t_lower, df=n_a + n_b - 2)

    # Upper bound test: H0: diff >= margin
    t_upper = (diff - equivalence_margin) / pooled_se
    p_upper = stats.t.cdf(t_upper, df=n_a + n_b - 2)

    # Equivalence is established if both p-values < alpha
    is_equivalent = bool(p_lower < alpha and p_upper < alpha)

    return {
        "t_statistic_lower": float(t_lower),
        "t_statistic_upper": float(t_upper),
        "p_value_lower": float(p_lower),
        "p_value_upper": float(p_upper),
        "equivalence_margin": float(equivalence_margin),
        "is_equivalent": is_equivalent,
        "alpha": alpha
    }


def benjamini_hochberg_correction(
    p_values: List[float],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Apply Benjamini-Hochberg correction for multiple comparisons.

    This function controls the False Discovery Rate (FDR) across a set of p-values.

    Args:
        p_values: List of raw p-values from multiple hypothesis tests.
        alpha: Target False Discovery Rate (FDR) level.

    Returns:
        Dictionary containing:
            - corrected_p_values: The BH-adjusted p-values.
            - is_significant: Boolean list indicating which tests are significant after correction.
            - n_significant: Number of significant tests.
            - threshold: The adaptive threshold used.
    """
    if not p_values:
        raise StatsError("p_values list cannot be empty.")

    if any(p < 0 or p > 1 for p in p_values):
        raise StatsError("All p-values must be between 0 and 1.")

    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p_values = np.array([p_values[i] for i in sorted_indices])

    # Calculate BH critical values
    # p_(i) <= (i/n) * alpha
    # To get corrected p-values: p_corrected[i] = min(1, min_{j>=i} (p_j * n / j))
    # We compute the adjusted p-values such that they are monotonically increasing
    adjusted_p_values = np.zeros(n)
    adjusted_p_values[-1] = sorted_p_values[-1] * n / n

    for i in range(n - 2, -1, -1):
        # The adjusted p-value is the minimum of the current scaled value
        # and the next adjusted p-value (to ensure monotonicity)
        current_scaled = sorted_p_values[i] * n / (i + 1)
        adjusted_p_values[i] = min(current_scaled, adjusted_p_values[i + 1])

    # Ensure no adjusted p-value exceeds 1.0
    adjusted_p_values = np.minimum(adjusted_p_values, 1.0)

    # Map back to original order
    final_adjusted_p_values = np.zeros(n)
    for idx, adj_val in zip(sorted_indices, adjusted_p_values):
        final_adjusted_p_values[idx] = adj_val

    # Determine significance
    is_significant = final_adjusted_p_values < alpha
    n_significant = int(np.sum(is_significant))

    # Calculate the effective threshold for the smallest significant p-value
    # The threshold is the largest (i/n)*alpha such that p_(i) <= (i/n)*alpha
    # For simplicity, we report the alpha level used
    threshold = alpha

    logger.info(f"Benjamini-Hochberg correction applied to {n} tests. "
                f"Found {n_significant} significant results at FDR={alpha}.")

    return {
        "raw_p_values": p_values,
        "corrected_p_values": list(final_adjusted_p_values),
        "is_significant": list(is_significant),
        "n_significant": n_significant,
        "n_total": n,
        "alpha": alpha,
        "method": "benjamini_hochberg_fdr"
    }


def main():
    """
    Main entry point for running statistical analyses.
    This function orchestrates the execution of various statistical tests
    and saves results to the designated output directory.
    """
    config = get_config()
    logger.info("Starting statistical analysis module.")

    # Example usage with dummy data (in real execution, data would be loaded from artifacts)
    # This is for demonstration of the API structure.
    # In a real run, data would come from sensitivity analysis or source localization outputs.
    dummy_data_a = np.random.normal(loc=0.5, scale=0.2, size=100)
    dummy_data_b = np.random.normal(loc=0.6, scale=0.2, size=100)

    # Run permutation test
    try:
        perm_result = mixed_effects_permutation_test(dummy_data_a, dummy_data_b)
        logger.info(f"Permutation test result: p={perm_result['p_value']:.4f}")
    except StatsError as e:
        logger.error(f"Permutation test failed: {e}")

    # Run t-test
    try:
        t_result = independent_samples_ttest(dummy_data_a, dummy_data_b)
        logger.info(f"T-test result: t={t_result['t_statistic']:.4f}, p={t_result['p_value']:.4f}")
    except StatsError as e:
        logger.error(f"T-test failed: {e}")

    # Run TOST
    try:
        tost_result = tost_equivalence_test(dummy_data_a, dummy_data_b)
        logger.info(f"TOST result: equivalent={tost_result['is_equivalent']}")
    except StatsError as e:
        logger.error(f"TOST failed: {e}")

    # Run BH correction on a set of dummy p-values (e.g., from multiple electrodes)
    dummy_p_values = [0.01, 0.04, 0.03, 0.005, 0.08, 0.02]
    try:
        bh_result = benjamini_hochberg_correction(dummy_p_values)
        logger.info(f"BH correction: {bh_result['n_significant']}/{bh_result['n_total']} significant")
    except StatsError as e:
        logger.error(f"BH correction failed: {e}")

    logger.info("Statistical analysis module execution complete.")


if __name__ == "__main__":
    main()