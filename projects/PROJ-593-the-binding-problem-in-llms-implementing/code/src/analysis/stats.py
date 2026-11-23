"""
Statistical analysis utilities for the binding problem research.

This module provides functions for statistical testing and correction,
including permutation tests and Bonferroni correction.
"""

import numpy as np
from scipy import stats as scipy_stats
from typing import List, Tuple, Union


def permute_test(
    x: np.ndarray,
    y: np.ndarray,
    n_permutations: int = 1000,
    alternative: str = "two-sided",
    seed: int = 42
) -> Tuple[float, float]:
    """
    Perform a permutation test to compare two samples.

    Args:
        x: First sample array.
        y: Second sample array.
        n_permutations: Number of permutation iterations (default >= 1000).
        alternative: Type of test ('two-sided', 'less', 'greater').
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (observed_statistic, p_value).
    """
    rng = np.random.default_rng(seed)
    x = np.asarray(x)
    y = np.asarray(y)

    # Calculate observed statistic (difference in means)
    observed_stat = np.mean(x) - np.mean(y)

    # Combine samples
    combined = np.concatenate([x, y])
    n_x = len(x)
    n_y = len(y)
    n_total = n_x + n_y

    # Generate permutation distribution
    perm_stats = np.zeros(n_permutations)
    for i in range(n_permutations):
        # Shuffle indices
        perm_indices = rng.permutation(n_total)
        perm_x = combined[perm_indices[:n_x]]
        perm_y = combined[perm_indices[n_x:]]
        perm_stats[i] = np.mean(perm_x) - np.mean(perm_y)

    # Calculate p-value
    if alternative == "two-sided":
        p_value = np.mean(np.abs(perm_stats) >= np.abs(observed_stat))
    elif alternative == "less":
        p_value = np.mean(perm_stats <= observed_stat)
    elif alternative == "greater":
        p_value = np.mean(perm_stats >= observed_stat)
    else:
        raise ValueError(f"Unknown alternative: {alternative}")

    return observed_stat, p_value


def bonferroni_correct(
    p_values: List[float],
    alpha: float = 0.05
) -> Tuple[List[float], List[bool]]:
    """
    Apply Bonferroni correction to a list of p-values.

    The Bonferroni correction controls the family-wise error rate by dividing
    the significance level alpha by the number of tests, or equivalently,
    multiplying each p-value by the number of tests.

    Args:
        p_values: List of raw p-values from statistical tests.
        alpha: Significance level (default 0.05).

    Returns:
        Tuple of (corrected_p_values, significant_flags).
        - corrected_p_values: List of Bonferroni-corrected p-values.
        - significant_flags: List of booleans indicating if the test is significant
          after correction (True if corrected_p_value < alpha).

    Raises:
        ValueError: If p_values is empty or contains invalid values.
    """
    if not p_values:
        raise ValueError("p_values list cannot be empty")

    n_tests = len(p_values)

    # Validate p-values
    for i, p in enumerate(p_values):
        if not (0.0 <= p <= 1.0):
            raise ValueError(f"Invalid p-value at index {i}: {p}. Must be between 0 and 1.")

    # Apply Bonferroni correction: p_corrected = p * n_tests
    corrected_p_values = [min(p * n_tests, 1.0) for p in p_values]

    # Determine significance
    significant_flags = [p_corr < alpha for p_corr in corrected_p_values]

    return corrected_p_values, significant_flags


def bonferroni_threshold(
    n_tests: int,
    alpha: float = 0.05
) -> float:
    """
    Calculate the Bonferroni-corrected significance threshold.

    This is a convenience function that returns alpha / n_tests,
    which is the threshold against which raw p-values can be compared.

    Args:
        n_tests: Number of statistical tests in the family.
        alpha: Significance level (default 0.05).

    Returns:
        The corrected significance threshold.
    """
    if n_tests <= 0:
        raise ValueError("n_tests must be a positive integer")

    return alpha / n_tests