"""
Statistical utilities for the bird migration analysis pipeline.

This module provides helper functions for:
- Benjamini-Hochberg FDR correction
- Bootstrapping for confidence intervals
- Permutation tests with early stopping logic
"""
import numpy as np
from typing import List, Tuple, Optional, Dict, Any, Callable
from joblib import Parallel, delayed
import json
import os
from scipy import stats
from src.lib.config import get_config

def benjamini_hochberg_fdr(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], List[bool]]:
    """
    Apply the Benjamini-Hochberg procedure to control the False Discovery Rate.

    Args:
        p_values: List of raw p-values.
        alpha: Significance level (default 0.05).

    Returns:
        A tuple containing:
        - adjusted_p_values: List of adjusted p-values.
        - is_significant: List of booleans indicating if the result is significant after FDR correction.
    """
    if not p_values:
        return [], []

    n = len(p_values)
    # Sort p-values while keeping track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p_values = np.array([p_values[i] for i in sorted_indices])

    # Calculate adjusted p-values
    # Formula: p_adj = p * n / i, where i is the rank (1-indexed)
    # Ensure monotonicity by taking the cumulative minimum from the end
    adjusted_p_values = sorted_p_values * n / (np.arange(1, n + 1))
    adjusted_p_values = np.minimum.accumulate(adjusted_p_values[::-1])[::-1]
    
    # Clamp values to [0, 1]
    adjusted_p_values = np.clip(adjusted_p_values, 0, 1)

    # Map back to original order
    final_adjusted = np.empty(n)
    final_adjusted[sorted_indices] = adjusted_p_values

    # Determine significance
    is_significant = final_adjusted <= alpha

    return final_adjusted.tolist(), is_significant.tolist()

def bootstrap_confidence_interval(
    data: np.ndarray, 
    statistic_func: Callable[[np.ndarray], float], 
    n_bootstrap: int = 1000, 
    confidence_level: float = 0.95, 
    random_state: Optional[int] = None
) -> Tuple[float, float, float]:
    """
    Calculate bootstrapped confidence intervals for a given statistic.

    Args:
        data: Input data array.
        statistic_func: Function to compute the statistic (e.g., mean, median).
        n_bootstrap: Number of bootstrap samples.
        confidence_level: Confidence level (e.g., 0.95 for 95% CI).
        random_state: Random seed for reproducibility.

    Returns:
        A tuple containing:
        - original_stat: The statistic calculated on the original data.
        - ci_lower: Lower bound of the confidence interval.
        - ci_upper: Upper bound of the confidence interval.
    """
    if random_state is not None:
        np.random.seed(random_state)

    n = len(data)
    bootstrap_stats = []

    for _ in range(n_bootstrap):
        # Resample with replacement
        sample_indices = np.random.choice(n, size=n, replace=True)
        sample = data[sample_indices]
        stat = statistic_func(sample)
        bootstrap_stats.append(stat)

    bootstrap_stats = np.array(bootstrap_stats)
    original_stat = statistic_func(data)

    alpha = 1 - confidence_level
    ci_lower = np.percentile(bootstrap_stats, 100 * (alpha / 2))
    ci_upper = np.percentile(bootstrap_stats, 100 * (1 - alpha / 2))

    return original_stat, ci_lower, ci_upper

def run_permutation_test_early_stop(
    data_x: np.ndarray, 
    data_y: np.ndarray, 
    n_permutations: int = 10000, 
    statistic_func: Optional[Callable[[np.ndarray, np.ndarray], float]] = None,
    alpha: float = 0.05,
    random_state: Optional[int] = None,
    early_stop_threshold: float = 0.001,
    early_stop_check_interval: int = 100
) -> Dict[str, Any]:
    """
    Run a permutation test with an early stopping flag for reporting.

    The function runs the FULL number of permutations regardless of the early stop flag.
    The flag is only for reporting if the interim p-value drops below the threshold.

    Args:
        data_x: First dataset array.
        data_y: Second dataset array.
        n_permutations: Total number of permutations to run (default 10000).
        statistic_func: Function to compute the test statistic (e.g., correlation). 
                        Defaults to Pearson correlation if None.
        alpha: Significance level.
        random_state: Random seed.
        early_stop_threshold: Threshold for interim p-value to set early_stop_flag.
        early_stop_check_interval: Check for early stopping every N permutations.

    Returns:
        A dictionary with:
        - observed_stat: Statistic on original data.
        - p_value: Calculated p-value.
        - n_permutations: Total permutations run.
        - early_stop_flag: Boolean indicating if interim p < threshold was met.
        - final_p_value: The final calculated p-value.
    """
    if random_state is not None:
        np.random.seed(random_state)

    if statistic_func is None:
        def statistic_func(x, y):
            return np.corrcoef(x, y)[0, 1]

    # Ensure arrays are float for calculation
    x = np.asarray(data_x, dtype=float)
    y = np.asarray(data_y, dtype=float)

    if len(x) != len(y):
        raise ValueError("Input arrays must have the same length.")

    # Calculate observed statistic
    observed_stat = statistic_func(x, y)

    count_extreme = 0
    early_stop_flag = False

    # Run full permutation test
    for i in range(n_permutations):
        # Shuffle y
        perm_y = np.random.permutation(y)
        perm_stat = statistic_func(x, perm_y)

        # Count extreme values (two-tailed or one-tailed based on context, assuming two-tailed here for generality)
        # Using absolute difference for two-tailed, or direct comparison for one-tailed.
        # Standard permutation test usually checks |stat| >= |obs| or stat >= obs.
        # Assuming we are testing if the relationship is stronger than random (absolute value)
        if abs(perm_stat) >= abs(observed_stat):
            count_extreme += 1

        # Check for early stop condition for reporting
        if (i + 1) % early_stop_check_interval == 0:
            interim_p = count_extreme / (i + 1)
            if interim_p < early_stop_threshold:
                early_stop_flag = True

    final_p_value = count_extreme / n_permutations

    return {
        "observed_stat": float(observed_stat),
        "p_value": final_p_value,
        "n_permutations": n_permutations,
        "early_stop_flag": early_stop_flag,
        "final_p_value": final_p_value
    }

def save_permutation_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save permutation test results to a JSON file.

    Args:
        results: Dictionary containing results from run_permutation_test_early_stop.
        output_path: Path to the output JSON file.
    """
    # Ensure directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
        f.write('\n')