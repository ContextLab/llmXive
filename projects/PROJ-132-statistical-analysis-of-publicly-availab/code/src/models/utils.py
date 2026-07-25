"""
Statistical utilities for the bird migration analysis pipeline.

This module provides helper functions for:
- Benjamini-Hochberg FDR correction
- Bootstrapping confidence intervals
- Permutation tests with early stopping logic
- Saving permutation results to disk
"""
import numpy as np
from typing import List, Tuple, Optional, Dict, Any, Callable
from joblib import Parallel, delayed
import json
import os
from scipy import stats
import logging

logger = logging.getLogger(__name__)


def benjamini_hochberg_fdr(p_values: List[float], alpha: float = 0.05) -> Tuple[List[bool], List[float]]:
    """
    Apply the Benjamini-Hochberg procedure to control the False Discovery Rate.

    Args:
        p_values: List of raw p-values from hypothesis tests.
        alpha: Target FDR level (default 0.05).

    Returns:
        A tuple containing:
        - List of booleans indicating which hypotheses are rejected (True = significant).
        - List of adjusted p-values (q-values).
    """
    if not p_values:
        return [], []

    n = len(p_values)
    # Sort p-values while keeping track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p_values = np.array([p_values[i] for i in sorted_indices])

    # Calculate BH critical values
    ranks = np.arange(1, n + 1)
    critical_values = (ranks / n) * alpha

    # Find the largest k such that p_(k) <= critical_value_(k)
    # We need to find the maximum index where the condition holds
    condition = sorted_p_values <= critical_values
    if not np.any(condition):
        # No rejections
        adjusted_p_values = np.minimum.accumulate(1.0 - sorted_p_values[::-1])[::-1]
        adjusted_p_values = np.minimum(adjusted_p_values, 1.0)
        return [False] * n, adjusted_p_values.tolist()

    # Find the largest index k where condition is true
    k = np.where(condition)[0][-1]

    # All hypotheses with rank <= k are rejected
    rejected = np.zeros(n, dtype=bool)
    rejected[sorted_indices[:k+1]] = True

    # Calculate adjusted p-values (q-values)
    # q_i = min( (n/i) * p_i, min_{j>i} ( (n/j) * p_j ) )
    # Using the cumulative minimum approach from the back
    adjusted_p_values = np.full(n, np.inf)
    for i in range(n - 1, -1, -1):
        adjusted_p_values[i] = min(
            (n / (i + 1)) * sorted_p_values[i],
            adjusted_p_values[i + 1] if i < n - 1 else np.inf
        )
    adjusted_p_values = np.minimum(adjusted_p_values, 1.0)

    return rejected.tolist(), adjusted_p_values.tolist()


def bootstrap_confidence_interval(
    data: np.ndarray,
    stat_func: Callable[[np.ndarray], float],
    n_bootstraps: int = 1000,
    confidence_level: float = 0.95,
    seed: Optional[int] = None
) -> Tuple[float, float, float]:
    """
    Calculate a bootstrap confidence interval for a given statistic.

    Args:
        data: The input data array.
        stat_func: A function that computes the statistic of interest from data.
        n_bootstraps: Number of bootstrap samples to generate.
        confidence_level: The confidence level (e.g., 0.95 for 95% CI).
        seed: Random seed for reproducibility.

    Returns:
        A tuple (point_estimate, lower_bound, upper_bound).
    """
    if seed is not None:
        np.random.seed(seed)

    n = len(data)
    bootstrap_stats = np.empty(n_bootstraps)

    for i in range(n_bootstraps):
        # Sample with replacement
        sample = np.random.choice(data, size=n, replace=True)
        bootstrap_stats[i] = stat_func(sample)

    point_estimate = stat_func(data)
    alpha = 1 - confidence_level
    lower_bound = np.percentile(bootstrap_stats, 100 * (alpha / 2))
    upper_bound = np.percentile(bootstrap_stats, 100 * (1 - alpha / 2))

    return point_estimate, lower_bound, upper_bound


def run_permutation_test_early_stop(
    x: np.ndarray,
    y: np.ndarray,
    n_shuffles: int = 10000,
    stat_func: Optional[Callable[[np.ndarray, np.ndarray], float]] = None,
    seed: Optional[int] = None,
    early_stop_threshold: float = 0.001,
    early_stop_check_interval: int = 100
) -> Dict[str, Any]:
    """
    Run a permutation test with early stopping logic for efficiency.

    This function tests the null hypothesis that there is no association between
    x and y. It supports early stopping if the p-value is clearly significant,
    but ALWAYS completes all n_shuffles permutations as required by the spec.

    Args:
        x: First variable array.
        y: Second variable array.
        n_shuffles: Total number of permutations to run (MUST complete all).
        stat_func: Function to compute test statistic (default: correlation).
        seed: Random seed for reproducibility.
        early_stop_threshold: If interim p-value drops below this, set early_stop_flag.
        early_stop_check_interval: Check for early stopping every N shuffles.

    Returns:
        Dictionary with keys:
        - "observed_stat": The test statistic for the original data.
        - "p_value": The two-sided p-value.
        - "n_shuffles": Total number of shuffles performed.
        - "early_stop_flag": True if interim p-value < threshold at any point.
        - "null_distribution": List of permuted statistics.
    """
    if seed is not None:
        np.random.seed(seed)

    if stat_func is None:
        def stat_func(a, b):
            return np.corrcoef(a, b)[0, 1]

    # Ensure arrays are same length
    min_len = min(len(x), len(y))
    x = x[:min_len]
    y = y[:min_len]

    observed_stat = stat_func(x, y)

    null_stats = []
    early_stop_flag = False

    for i in range(n_shuffles):
        # Shuffle y
        shuffled_y = np.random.permutation(y)
        perm_stat = stat_func(x, shuffled_y)
        null_stats.append(perm_stat)

        # Check for early stopping condition
        if (i + 1) % early_stop_check_interval == 0:
            count_extreme = sum(1 for s in null_stats if abs(s) >= abs(observed_stat))
            interim_p = count_extreme / (i + 1)

            if interim_p < early_stop_threshold:
                early_stop_flag = True
                logger.info(f"Early stopping condition met at shuffle {i+1}: interim p={interim_p:.4f}")
                # Note: We do NOT break here. The spec requires full completion.

    # Calculate final p-value
    count_extreme = sum(1 for s in null_stats if abs(s) >= abs(observed_stat))
    final_p_value = count_extreme / n_shuffles

    return {
        "observed_stat": observed_stat,
        "p_value": final_p_value,
        "n_shuffles": n_shuffles,
        "early_stop_flag": early_stop_flag,
        "null_distribution": null_stats
    }


def save_permutation_results(
    results: Dict[str, Any],
    output_path: str,
    species: str,
    coefficient: str
) -> None:
    """
    Save permutation test results to a JSON file.

    Args:
        results: Dictionary containing permutation test results.
        output_path: Path to the output JSON file.
        species: Species name for the results.
        coefficient: Name of the coefficient being tested.
    """
    output_data = {
        "species": species,
        "coefficient": coefficient,
        "p_value": results["p_value"],
        "n_shuffles": results["n_shuffles"],
        "early_stop_flag": results["early_stop_flag"],
        "final_p_value": results["p_value"],
        "observed_stat": results["observed_stat"]
    }

    # Ensure directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Load existing results if file exists
    all_results = []
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r') as f:
                all_results = json.load(f)
        except (json.JSONDecodeError, IOError):
            all_results = []

    # Append new result
    all_results.append(output_data)

    # Write back
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2)

    logger.info(f"Saved permutation results for {species} ({coefficient}) to {output_path}")