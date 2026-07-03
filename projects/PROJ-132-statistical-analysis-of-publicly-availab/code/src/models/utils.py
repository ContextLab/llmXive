"""
Statistical utility functions for the bird migration analysis pipeline.

This module provides:
- Benjamini-Hochberg FDR correction for multiple hypothesis testing.
- Bootstrapping logic for confidence interval estimation.
- Early-stopping logic for permutation tests (with full execution guarantee).
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from joblib import Parallel, delayed
import json
import os


def benjamini_hochberg_fdr(p_values: List[float], alpha: float = 0.05) -> Tuple[List[bool], List[float]]:
    """
    Apply the Benjamini-Hochberg procedure to control the False Discovery Rate.

    Args:
        p_values: List of raw p-values from hypothesis tests.
        alpha: Desired FDR level (default 0.05).

    Returns:
        A tuple containing:
        - List of booleans indicating which hypotheses are rejected (True) or not (False).
        - List of adjusted p-values (q-values).
    """
    if not p_values:
        return [], []

    n = len(p_values)
    # Sort p-values while keeping track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array([p_values[i] for i in sorted_indices])

    # Calculate BH critical values
    ranks = np.arange(1, n + 1)
    critical_values = (ranks / n) * alpha

    # Find the largest k such that p_(k) <= critical_value_(k)
    # We iterate backwards to find the threshold
    threshold_idx = -1
    for i in range(n - 1, -1, -1):
        if sorted_p[i] <= critical_values[i]:
            threshold_idx = i
            break

    if threshold_idx == -1:
        # No rejections
        return [False] * n, [1.0] * n

    # Calculate adjusted p-values (q-values)
    # q_i = min(1, min_{j >= i} (n * p_j / j))
    # We compute this in a way that ensures monotonicity
    q_values = np.zeros(n)
    min_q = 1.0
    for i in range(n - 1, -1, -1):
        q = sorted_p[i] * n / (i + 1)
        min_q = min(min_q, q)
        q_values[i] = min(1.0, min_q)

    # Map back to original order
    adjusted_p_values = [0.0] * n
    for idx, q in zip(sorted_indices, q_values):
        adjusted_p_values[idx] = q

    # Determine rejections based on original p-values and threshold
    # A hypothesis is rejected if its adjusted p-value <= alpha
    rejections = [q <= alpha for q in adjusted_p_values]

    return rejections, adjusted_p_values


def bootstrap_confidence_interval(
    data: np.ndarray,
    statistic_func,
    n_bootstraps: int = 1000,
    confidence_level: float = 0.95,
    random_seed: Optional[int] = None
) -> Tuple[float, float, float]:
    """
    Compute a bootstrap confidence interval for a given statistic.

    Args:
        data: Input data array.
        statistic_func: Function that computes the statistic of interest from a sample.
        n_bootstraps: Number of bootstrap resamples to generate.
        confidence_level: Confidence level for the interval (e.g., 0.95).
        random_seed: Random seed for reproducibility.

    Returns:
        A tuple containing:
        - Point estimate (statistic on original data).
        - Lower bound of the confidence interval.
        - Upper bound of the confidence interval.
    """
    if random_seed is not None:
        np.random.seed(random_seed)

    n = len(data)
    boot_stats = np.zeros(n_bootstraps)

    for i in range(n_bootstraps):
        # Resample with replacement
        resample_indices = np.random.randint(0, n, n)
        resample = data[resample_indices]
        boot_stats[i] = statistic_func(resample)

    point_estimate = statistic_func(data)
    alpha = 1 - confidence_level
    lower_percentile = (alpha / 2) * 100
    upper_percentile = (1 - alpha / 2) * 100

    lower_bound = np.percentile(boot_stats, lower_percentile)
    upper_bound = np.percentile(boot_stats, upper_percentile)

    return point_estimate, lower_bound, upper_bound


def run_permutation_test_early_stop(
    observed_stat: float,
    data_x: np.ndarray,
    data_y: np.ndarray,
    statistic_func,
    n_shuffles: int = 10000,
    early_stop_threshold: float = 0.001,
    early_stop_n: int = 100,
    random_seed: Optional[int] = None,
    n_jobs: int = -1
) -> Dict[str, Any]:
    """
    Run a permutation test with early stopping logic for reporting,
    but always completing the full number of shuffles.

    Args:
        observed_stat: The observed statistic from the original data.
        data_x: First variable array.
        data_y: Second variable array.
        statistic_func: Function to compute the test statistic (e.g., correlation).
        n_shuffles: Total number of permutations to run (MUST complete all).
        early_stop_threshold: P-value threshold to trigger early stop flag.
        early_stop_n: Number of initial shuffles before checking for early stop.
        random_seed: Random seed for reproducibility.
        n_jobs: Number of parallel jobs for joblib (-1 means all cores).

    Returns:
        Dictionary with:
        - "p_value": Final p-value.
        - "n_shuffles": Total shuffles run.
        - "early_stop_flag": True if interim p < threshold at early_stop_n, else False.
        - "final_p_value": Same as p_value (explicitly named for clarity).
    """
    if random_seed is not None:
        np.random.seed(random_seed)

    n = len(data_x)
    combined = np.column_stack((data_x, data_y))

    def shuffle_and_compute(_):
        # Shuffle data_y indices
        perm_indices = np.random.permutation(n)
        shuffled_y = data_y[perm_indices]
        return statistic_func(data_x, shuffled_y)

    # Run all shuffles in parallel for efficiency
    null_stats = Parallel(n_jobs=n_jobs)(
        delayed(shuffle_and_compute)(i) for i in range(n_shuffles)
    )
    null_stats = np.array(null_stats)

    # Calculate two-sided p-value
    extreme_count = np.sum(np.abs(null_stats) >= np.abs(observed_stat))
    p_value = extreme_count / n_shuffles

    # Early stopping logic: check after first N shuffles (simulated for reporting)
    # In a real streaming scenario, we'd check incrementally. Here we simulate the check
    # using the first `early_stop_n` values of the null distribution.
    early_stop_flag = False
    if n_shuffles >= early_stop_n:
        interim_null = null_stats[:early_stop_n]
        interim_extreme = np.sum(np.abs(interim_null) >= np.abs(observed_stat))
        interim_p = interim_extreme / early_stop_n
        if interim_p < early_stop_threshold:
            early_stop_flag = True

    return {
        "p_value": float(p_value),
        "n_shuffles": n_shuffles,
        "early_stop_flag": early_stop_flag,
        "final_p_value": float(p_value)
    }


def save_permutation_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save permutation test results to a JSON file.

    Args:
        results: Dictionary containing results from run_permutation_test_early_stop.
        output_path: Path to the output JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)