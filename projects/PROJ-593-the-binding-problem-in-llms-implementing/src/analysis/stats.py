"""
Statistical analysis utilities for the binding problem research.

This module provides permutation test engines and multiple comparison correction
methods to validate the significance of observed oscillatory synchronization effects.
"""

import numpy as np
from scipy.stats import ttest_rel
from typing import Union, Tuple, List, Optional


def permute_test(
    data_a: Union[np.ndarray, List[float]],
    data_b: Union[np.ndarray, List[float]],
    n_iterations: int = 1000,
    statistic_func: Optional[str] = None,
    alternative: str = "two-sided",
    seed: Optional[int] = None,
) -> Tuple[float, float, np.ndarray]:
    """
    Perform a permutation test to assess the significance of the difference
    between two distributions.

    This function implements a non-parametric test that generates a null
    distribution by randomly shuffling labels between the two groups. It
    is robust to non-normal data distributions often encountered in neural
    signal analysis.

    Args:
        data_a: First group of observations (e.g., oscillatory model metrics).
        data_b: Second group of observations (e.g., baseline model metrics).
        n_iterations: Number of permutations to perform (default 1000).
        statistic_func: The name of the statistic to compute. Options:
            - "mean_diff": Difference in means (default).
            - "t_stat": Paired t-statistic (requires equal length).
            - "median_diff": Difference in medians.
            - If None, defaults to "mean_diff".
        alternative: The alternative hypothesis. One of:
            - "two-sided": Difference is not equal to 0.
            - "greater": Group A > Group B.
            - "less": Group A < Group B.
        seed: Random seed for reproducibility.

    Returns:
        A tuple containing:
            - p_value: The two-sided p-value from the permutation test.
            - observed_stat: The observed statistic calculated on the original data.
            - null_distribution: Array of statistics from the permuted data.

    Raises:
        ValueError: If input arrays are empty or if n_iterations < 1.
        TypeError: If inputs cannot be converted to numpy arrays.
    """
    if seed is not None:
        np.random.seed(seed)

    # Convert inputs to numpy arrays
    arr_a = np.asarray(data_a, dtype=float)
    arr_b = np.asarray(data_b, dtype=float)

    if arr_a.size == 0 or arr_b.size == 0:
        raise ValueError("Input arrays cannot be empty.")

    if n_iterations < 1:
        raise ValueError("n_iterations must be at least 1.")

    # Determine statistic function
    if statistic_func is None:
        statistic_func = "mean_diff"

    def compute_stat(x, y):
        if statistic_func == "mean_diff":
            return np.mean(x) - np.mean(y)
        elif statistic_func == "median_diff":
            return np.median(x) - np.median(y)
        elif statistic_func == "t_stat":
            if len(x) != len(y):
                raise ValueError("t_stat requires equal length arrays.")
            # Using scipy ttest_rel for paired, but we just need the statistic
            # Note: ttest_rel returns (statistic, pvalue). We want statistic.
            stat, _ = ttest_rel(x, y)
            return stat
        else:
            raise ValueError(f"Unknown statistic_func: {statistic_func}")

    # Compute observed statistic
    observed_stat = compute_stat(arr_a, arr_b)

    # Combine data for permutation
    combined = np.concatenate([arr_a, arr_b])
    n_a = len(arr_a)
    n_b = len(arr_b)
    n_total = n_a + n_b

    # Pre-allocate null distribution
    null_distribution = np.zeros(n_iterations)

    # Perform permutations
    for i in range(n_iterations):
        # Shuffle indices
        shuffled_indices = np.random.permutation(n_total)
        # Split shuffled data
        perm_a = combined[shuffled_indices[:n_a]]
        perm_b = combined[shuffled_indices[n_a:]]
        # Compute statistic
        null_distribution[i] = compute_stat(perm_a, perm_b)

    # Calculate p-value
    if alternative == "two-sided":
        # Count how many permuted stats are as extreme or more extreme than observed
        # Use absolute values for two-sided
        extreme_count = np.sum(np.abs(null_distribution) >= np.abs(observed_stat))
        p_value = (extreme_count + 1) / (n_iterations + 1)
    elif alternative == "greater":
        extreme_count = np.sum(null_distribution >= observed_stat)
        p_value = (extreme_count + 1) / (n_iterations + 1)
    elif alternative == "less":
        extreme_count = np.sum(null_distribution <= observed_stat)
        p_value = (extreme_count + 1) / (n_iterations + 1)
    else:
        raise ValueError(f"Invalid alternative: {alternative}")

    return p_value, observed_stat, null_distribution


def bonferroni_correct(
    p_values: Union[List[float], np.ndarray],
    n_tests: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply Bonferroni correction to a list of p-values to control the family-wise error rate.

    This is critical when performing multiple comparisons (e.g., across frequency bands,
    layers, or heads) to reduce the likelihood of false positives.

    Args:
        p_values: A list or array of raw p-values.
        n_tests: The number of tests performed. If None, defaults to len(p_values).

    Returns:
        A tuple containing:
            - corrected_p_values: The Bonferroni-corrected p-values (capped at 1.0).
            - is_significant: Boolean array indicating which tests are significant
              at alpha=0.05 after correction.

    Raises:
        ValueError: If p_values is empty.
    """
    p_arr = np.asarray(p_values, dtype=float)

    if p_arr.size == 0:
        raise ValueError("p_values cannot be empty.")

    if n_tests is None:
        n_tests = len(p_arr)

    if n_tests < 1:
        raise ValueError("n_tests must be at least 1.")

    # Bonferroni correction: p_corrected = p_raw * n_tests
    corrected = p_arr * n_tests
    # Cap at 1.0
    corrected = np.minimum(corrected, 1.0)

    # Determine significance at alpha=0.05
    is_sig = corrected < 0.05

    return corrected, is_sig
