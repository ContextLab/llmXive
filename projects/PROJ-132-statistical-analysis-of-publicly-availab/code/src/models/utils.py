"""
Statistical utilities for the bird migration climate correlation pipeline.

This module provides helpers for:
- Benjamini-Hochberg FDR correction
- Bootstrapping confidence intervals
- Permutation tests with early stopping logic
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any, Callable
from joblib import Parallel, delayed
import json
import os
from scipy import stats


def benjamini_hochberg_fdr(p_values: List[float], alpha: float = 0.05) -> Tuple[List[bool], List[float]]:
    """
    Apply the Benjamini-Hochberg procedure to control the False Discovery Rate.

    Args:
        p_values: List of raw p-values from hypothesis tests.
        alpha: Desired FDR level (default 0.05).

    Returns:
        A tuple containing:
        - List of booleans indicating which hypotheses are rejected (True = significant).
        - List of adjusted p-values.
    """
    if not p_values:
        return [], []

    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_pvals = np.array([p_values[i] for i in sorted_indices])

    # Calculate adjusted p-values
    # BH procedure: p_adj[i] = min(p_adj[i+1], p_raw[i] * n / (i+1))
    # We compute cumulatively from the largest p-value to ensure monotonicity
    rank = np.arange(1, n + 1)
    adjusted = sorted_pvals * n / rank

    # Enforce monotonicity: adjusted p-values must be non-decreasing with rank
    # We do this by taking the cumulative minimum from the end
    for i in range(n - 2, -1, -1):
        adjusted[i] = min(adjusted[i], adjusted[i + 1])

    # Ensure no adjusted p-value exceeds 1.0
    adjusted = np.minimum(adjusted, 1.0)

    # Determine rejections
    # A hypothesis is rejected if its adjusted p-value <= alpha
    # But we must map back to original order
    rejections = np.zeros(n, dtype=bool)
    for i, idx in enumerate(sorted_indices):
        if adjusted[i] <= alpha:
            rejections[idx] = True

    return rejections.tolist(), adjusted.tolist()


def bootstrap_confidence_interval(
    data: np.ndarray,
    stat_func: Callable[[np.ndarray], float],
    n_bootstrap: int = 1000,
    confidence_level: float = 0.95,
    random_state: Optional[int] = None
) -> Tuple[float, float, float]:
    """
    Compute a bootstrap confidence interval for a given statistic.

    Args:
        data: 1D array of observed data points.
        stat_func: Function that computes the statistic of interest from a sample.
        n_bootstrap: Number of bootstrap resamples.
        confidence_level: Confidence level for the interval (e.g., 0.95).
        random_state: Random seed for reproducibility.

    Returns:
        A tuple containing:
        - Point estimate of the statistic on original data.
        - Lower bound of the confidence interval.
        - Upper bound of the confidence interval.
    """
    if random_state is not None:
        rng = np.random.default_rng(random_state)
    else:
        rng = np.random.default_rng()

    point_estimate = stat_func(data)
    bootstrap_stats = []

    n = len(data)
    for _ in range(n_bootstrap):
        resample = rng.choice(data, size=n, replace=True)
        bootstrap_stats.append(stat_func(resample))

    bootstrap_stats = np.array(bootstrap_stats)
    alpha = 1 - confidence_level
    lower_idx = int((alpha / 2) * n_bootstrap)
    upper_idx = int((1 - alpha / 2) * n_bootstrap)

    lower_bound = np.percentile(bootstrap_stats, (alpha / 2) * 100)
    upper_bound = np.percentile(bootstrap_stats, (1 - alpha / 2) * 100)

    return point_estimate, lower_bound, upper_bound


def run_permutation_test_early_stop(
    observed_stat: float,
    null_distr_func: Callable[[], float],
    n_shuffles: int,
    alpha: float = 0.05,
    early_stop_threshold: float = 0.001,
    early_stop_check_interval: int = 100,
    n_jobs: int = -1,
    random_state: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run a permutation test with early stopping logic for efficiency.

    The test runs a minimum of `early_stop_check_interval` shuffles, then checks
    at intervals. If the interim p-value drops below `early_stop_threshold`,
    it sets an early_stop_flag but CONTINUES to run the full `n_shuffles`.
    This flag is for reporting/logging only; the full permutation count is always achieved.

    Args:
        observed_stat: The observed test statistic.
        null_distr_func: A function that returns a single random null statistic.
        n_shuffles: Total number of permutations to run.
        alpha: Significance level for final decision.
        early_stop_threshold: Threshold for triggering early_stop_flag.
        early_stop_check_interval: How often to check for early stopping.
        n_jobs: Number of parallel jobs (-1 for all CPUs).
        random_state: Random seed.

    Returns:
        Dictionary with:
        - 'observed_stat': The observed statistic.
        - 'p_value': Final p-value.
        - 'n_shuffles': Total shuffles run.
        - 'early_stop_flag': True if p-value dropped below threshold at any point.
        - 'final_p_value': Same as p_value (explicit for clarity).
    """
    if random_state is not None:
        np.random.seed(random_state)

    # Generate all null statistics in parallel
    null_stats = Parallel(n_jobs=n_jobs)(
        delayed(null_distr_func)() for _ in range(n_shuffles)
    )
    null_stats = np.array(null_stats)

    # Calculate p-value (two-sided or one-sided depending on context, assuming one-sided here: >)
    # P = (count of null >= observed + 1) / (n + 1)
    # Using standard permutation test formula
    extreme_count = np.sum(null_stats >= observed_stat)
    p_value = (extreme_count + 1) / (n_shuffles + 1)

    # Early stopping logic simulation (since we ran all in parallel, we check the cumulative distribution)
    # To strictly follow the "check at intervals" requirement, we simulate the check
    early_stop_flag = False
    current_extreme = 0
    for i in range(early_stop_check_interval, n_shuffles + 1, early_stop_check_interval):
        subset = null_stats[:i]
        current_extreme = np.sum(subset >= observed_stat)
        interim_p = (current_extreme + 1) / (i + 1)
        if interim_p < early_stop_threshold:
            early_stop_flag = True
            break  # We found the condition, flag it, but we already ran all

    return {
        "observed_stat": float(observed_stat),
        "p_value": float(p_value),
        "n_shuffles": n_shuffles,
        "early_stop_flag": bool(early_stop_flag),
        "final_p_value": float(p_value)
    }


def save_permutation_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save permutation test results to a JSON file.

    Args:
        results: Dictionary containing permutation test results.
        output_path: Path to the output JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)