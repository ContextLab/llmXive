"""
Statistics Utilities for User Story 3.

This module provides functions for bootstrap analysis, t-tests, and saving
statistical results. It is used by T030a, T030c, and T031.
"""

import os
import sys
import json
import time
import signal
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from scipy import stats


class TimeoutError(Exception):
    pass


def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")


def setup_timeout(seconds: int):
    """Set up a signal-based timeout."""
    if os.name == 'posix':
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)
    else:
        # Windows doesn't support SIGALRM, use a different mechanism or skip
        pass


def cancel_timeout():
    """Cancel the active timeout."""
    if os.name == 'posix':
        signal.alarm(0)


def calculate_effect_size(sample1: np.ndarray, sample2: np.ndarray) -> float:
    """
    Calculate Cohen's d effect size between two samples.
    """
    n1, n2 = len(sample1), len(sample2)
    mean1, mean2 = np.mean(sample1), np.mean(sample2)
    var1, var2 = np.var(sample1, ddof=1), np.var(sample2, ddof=1)

    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))

    if pooled_std == 0:
        return 0.0

    return (mean1 - mean2) / pooled_std


def bootstrap_power_analysis(
    sample1: np.ndarray,
    sample2: np.ndarray,
    n_iterations: int = 1000,
    alpha: float = 0.05,
    target_power: float = 0.8,
    max_time_seconds: float = 1800.0  # 30 minutes
) -> Dict[str, Any]:
    """
    Perform bootstrap hypothesis test with power analysis.

    Returns a dictionary with p-value, confidence interval, power, and samples used.
    """
    start_time = time.time()
    n1, n2 = len(sample1), len(sample2)

    # Observed difference
    obs_diff = np.mean(sample1) - np.mean(sample2)

    # Bootstrap resampling
    bootstrap_diffs = []

    for i in range(n_iterations):
        if time.time() - start_time > max_time_seconds:
            # Save partial results
            return {
                "status": "partial",
                "p_value": None,
                "confidence_interval": None,
                "power": None,
                "samples_used": i,
                "iterations_completed": i,
                "reason": "Time limit exceeded"
            }

        resample1 = np.random.choice(sample1, size=n1, replace=True)
        resample2 = np.random.choice(sample2, size=n2, replace=True)
        diff = np.mean(resample1) - np.mean(resample2)
        bootstrap_diffs.append(diff)

    bootstrap_diffs = np.array(bootstrap_diffs)

    # Calculate p-value (two-tailed)
    # Count how many bootstrap diffs are as extreme or more extreme than observed
    extreme_count = np.sum(np.abs(bootstrap_diffs) >= np.abs(obs_diff))
    p_value = extreme_count / n_iterations

    # Confidence interval (percentile method)
    ci_low = np.percentile(bootstrap_diffs, 100 * alpha / 2)
    ci_high = np.percentile(bootstrap_diffs, 100 * (1 - alpha / 2))

    # Estimate power (simplified: proportion of bootstrap CIs that exclude 0)
    # This is a rough estimate; a more rigorous power analysis would require
    # simulating under the alternative hypothesis.
    # For this implementation, we'll use the proportion of bootstrap samples
    # where the difference is significant.
    power_estimate = np.sum(np.abs(bootstrap_diffs) > np.abs(obs_diff) * 0.5) / n_iterations

    return {
        "status": "completed",
        "p_value": float(p_value),
        "confidence_interval": [float(ci_low), float(ci_high)],
        "power": float(power_estimate),
        "samples_used": len(sample1) + len(sample2),
        "iterations_completed": n_iterations,
        "observed_difference": float(obs_diff),
        "effect_size": float(calculate_effect_size(sample1, sample2))
    }


def run_bootstrap_test(
    fid_scores_tree: np.ndarray,
    fid_scores_teacher: np.ndarray,
    target_power: float = 0.8,
    max_time_seconds: float = 1800.0
) -> Dict[str, Any]:
    """
    Run bootstrap test on FID scores with adaptive sample size.
    """
    # Start with full dataset
    n_iterations = 1000
    result = bootstrap_power_analysis(
        fid_scores_tree, fid_scores_teacher,
        n_iterations=n_iterations,
        target_power=target_power,
        max_time_seconds=max_time_seconds
    )

    # If power is insufficient and we have time, increase iterations
    # Note: In a real scenario, we might increase the sample size by adding more data,
    # but here we are limited by the dataset size. We can only increase iterations.
    while result.get("power", 0) < target_power and result.get("status") != "partial":
        if time.time() - (time.time() - max_time_seconds) > max_time_seconds / 2:
            # If we've spent half the time and still not enough power, stop
            result["status"] = "partial"
            result["reason"] = "Power insufficient within time budget"
            break

        n_iterations += 500
        result = bootstrap_power_analysis(
            fid_scores_tree, fid_scores_teacher,
            n_iterations=n_iterations,
            target_power=target_power,
            max_time_seconds=max_time_seconds
        )

    return result


def run_ttest(
    clip_scores_tree: np.ndarray,
    clip_scores_teacher: np.ndarray,
    target_power: float = 0.8,
    max_time_seconds: float = 1800.0
) -> Dict[str, Any]:
    """
    Run paired t-test on CLIP scores with power analysis.
    """
    start_time = time.time()

    # Perform paired t-test
    t_stat, p_value = stats.ttest_rel(clip_scores_tree, clip_scores_teacher)

    # Calculate effect size (Cohen's d for paired samples)
    diff = clip_scores_tree - clip_scores_teacher
    d = np.mean(diff) / np.std(diff, ddof=1)

    # Estimate power (simplified)
    # For a t-test, power depends on effect size, sample size, and alpha.
    # We'll use a simple heuristic: if effect size is large and p-value is small, power is high.
    # A more rigorous calculation would use scipy.stats.ttest_power or similar.
    # Here we estimate based on the non-centrality parameter.
    n = len(clip_scores_tree)
    alpha = 0.05
    # Approximate power calculation
    # This is a simplification; for exact power, use statsmodels or similar.
    power_estimate = 1.0 - (p_value if p_value < 1.0 else 0.0)  # Rough heuristic

    result = {
        "status": "completed",
        "p_value": float(p_value),
        "t_statistic": float(t_stat),
        "effect_size": float(d),
        "power": float(power_estimate),
        "samples_used": n,
        "confidence_interval": None  # Could calculate CI for mean difference
    }

    # Check if we need to increase sample size (if we had more data)
    # Since we are using the full dataset, we can't increase n.
    # We just return the result.

    return result


def save_partial_results(
    results: Dict[str, Any],
    output_path: Path,
    status: str = "partial"
):
    """
    Save partial results to a JSON file.
    """
    results["status"] = status
    results["saved_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)


def save_statistical_tests(
    results: Dict[str, Any],
    output_path: Path
):
    """
    Save final statistical test results to a JSON file.
    """
    results["saved_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)


def load_bootstrap_results(input_path: Path) -> Dict[str, Any]:
    """
    Load bootstrap results from a JSON file.
    """
    with open(input_path, 'r') as f:
        return json.load(f)


def load_ttest_results(input_path: Path) -> Dict[str, Any]:
    """
    Load t-test results from a JSON file.
    """
    with open(input_path, 'r') as f:
        return json.load(f)