import numpy as np
from typing import List, Tuple, Optional, Dict, Any, Callable
from joblib import Parallel, delayed
import json
import os
import time
from scipy import stats

from src.config import setup_logging

logger = setup_logging(__name__)


def benjamini_hochberg_fdr(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.

    Args:
        p_values: List of raw p-values.
        alpha: Significance level.

    Returns:
        List of adjusted q-values.
    """
    n = len(p_values)
    if n == 0:
        return []

    sorted_indices = np.argsort(p_values)
    sorted_p_values = np.array(p_values)[sorted_indices]

    # Calculate BH critical values
    critical_values = sorted_p_values * n / (np.arange(1, n + 1) + 1e-10)

    # Find the largest k where p_(k) <= critical value
    valid = sorted_p_values <= critical_values
    if not np.any(valid):
        adjusted = np.ones(n) * alpha
    else:
        k = np.where(valid)[0][-1]
        # Back-fill adjusted values
        adjusted = np.ones(n) * alpha
        adjusted[:k+1] = sorted_p_values[:k+1] * n / (np.arange(1, k+2) + 1e-10)

    # Restore original order
    final_adjusted = np.zeros(n)
    final_adjusted[sorted_indices] = np.minimum.accumulate(adjusted[::-1])[::-1]

    return final_adjusted.tolist()


def bootstrap_confidence_interval(
    data: np.ndarray,
    stat_func: Callable[[np.ndarray], float],
    n_bootstraps: int = 1000,
    confidence_level: float = 0.95,
    random_state: Optional[int] = None
) -> Tuple[float, float]:
    """
    Calculate bootstrap confidence interval for a statistic.

    Args:
        data: Input data array.
        stat_func: Function to compute the statistic.
        n_bootstraps: Number of bootstrap samples.
        confidence_level: Confidence level (e.g., 0.95).
        random_state: Random seed for reproducibility.

    Returns:
        Tuple of (lower_bound, upper_bound).
    """
    rng = np.random.default_rng(random_state)
    n = len(data)
    bootstrap_stats = []

    for _ in range(n_bootstraps):
        sample = rng.choice(data, size=n, replace=True)
        bootstrap_stats.append(stat_func(sample))

    bootstrap_stats = np.array(bootstrap_stats)
    lower = np.percentile(bootstrap_stats, (1 - confidence_level) / 2 * 100)
    upper = np.percentile(bootstrap_stats, (1 + confidence_level) / 2 * 100)

    return lower, upper


def run_permutation_test_early_stop(
    data: np.ndarray,
    labels: np.ndarray,
    stat_func: Callable[[np.ndarray, np.ndarray], float],
    n_permutations: int = 10000,
    alpha: float = 0.05,
    random_state: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run a permutation test with early stopping.

    Args:
        data: Data array.
        labels: Group labels.
        stat_func: Function computing the test statistic (data, labels).
        n_permutations: Maximum number of permutations.
        alpha: Significance level.
        random_state: Random seed.

    Returns:
        Dictionary with observed_stat, p_value, n_permutations_run.
    """
    rng = np.random.default_rng(random_state)
    observed_stat = stat_func(data, labels)

    count_extreme = 0
    n_run = 0

    for i in range(n_permutations):
        perm_labels = rng.permutation(labels)
        perm_stat = stat_func(data, perm_labels)

        if abs(perm_stat) >= abs(observed_stat):
            count_extreme += 1

        n_run += 1

        # Early stopping: if p-value estimate is clearly above alpha
        current_p = (count_extreme + 1) / (n_run + 1)
        if current_p > alpha and n_run > 100:
            # Check if we are far enough above alpha to stop
            # Conservative check: if current_p > alpha + margin
            margin = 0.02
            if current_p > alpha + margin:
                logger.info(f"Early stopping at permutation {n_run}: p={current_p:.4f} > alpha={alpha}")
                break

    final_p = (count_extreme + 1) / (n_run + 1)

    return {
        "observed_stat": observed_stat,
        "p_value": final_p,
        "n_permutations_run": n_run
    }


def save_permutation_results(
    results: List[Dict[str, Any]],
    output_path: str
) -> None:
    """
    Save permutation test results to a JSON file.

    Args:
        results: List of result dictionaries.
        output_path: Path to output JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved permutation results to {output_path}")


def bootstrap_trajectory_confidence_intervals(
    trajectory_shifts: List[float],
    n_bootstraps: int = 1000,
    confidence_level: float = 0.95,
    random_state: Optional[int] = None
) -> Dict[str, float]:
    """
    Calculate bootstrap confidence intervals for trajectory shifts.

    Args:
        trajectory_shifts: List of shift magnitudes.
        n_bootstraps: Number of bootstrap samples.
        confidence_level: Confidence level.
        random_state: Random seed.

    Returns:
        Dictionary with mean, ci_lower, ci_upper.
    """
    data = np.array(trajectory_shifts)
    lower, upper = bootstrap_confidence_interval(
        data,
        stat_func=np.mean,
        n_bootstraps=n_bootstraps,
        confidence_level=confidence_level,
        random_state=random_state
    )

    return {
        "mean": float(np.mean(data)),
        "ci_lower": float(lower),
        "ci_upper": float(upper)
    }


def benchmark_permutation(
    data: np.ndarray,
    labels: np.ndarray,
    stat_func: Callable[[np.ndarray, np.ndarray], float],
    n_shuffles: int = 1000,
    chunk_size: int = 100,
    random_state: Optional[int] = None
) -> Dict[str, float]:
    """
    Benchmark permutation test runtime to estimate time for full shuffles.

    Runs a subset of permutations and extrapolates runtime.

    Args:
        data: Data array.
        labels: Group labels.
        stat_func: Function computing the test statistic.
        n_shuffles: Number of shuffles to run for benchmarking.
        chunk_size: Number of shuffles per chunk.
        random_state: Random seed.

    Returns:
        Dictionary with benchmark results:
        - time_per_shuffle: Average time per shuffle (seconds)
        - estimated_total_time: Estimated time for full permutations (seconds)
        - n_shuffles_run: Actual number of shuffles run
    """
    rng = np.random.default_rng(random_state)
    observed_stat = stat_func(data, labels)

    total_time = 0.0
    n_run = 0

    num_chunks = (n_shuffles + chunk_size - 1) // chunk_size

    logger.info(f"Starting benchmark with {n_shuffles} shuffles in chunks of {chunk_size}")

    for i in range(num_chunks):
        start_time = time.time()
        chunk_end = min((i + 1) * chunk_size, n_shuffles)
        current_chunk_size = chunk_end - (i * chunk_size)

        for _ in range(current_chunk_size):
            perm_labels = rng.permutation(labels)
            _ = stat_func(data, perm_labels)

        end_time = time.time()
        chunk_time = end_time - start_time
        total_time += chunk_time
        n_run += current_chunk_size

    time_per_shuffle = total_time / n_run if n_run > 0 else 0.0
    estimated_total_time = time_per_shuffle * 10000  # Estimate for 10k shuffles

    result = {
        "time_per_shuffle": time_per_shuffle,
        "estimated_total_time": estimated_total_time,
        "n_shuffles_run": n_run,
        "chunk_size": chunk_size,
        "benchmark_shuffles": n_shuffles
    }

    logger.info(f"Benchmark complete: {n_run} shuffles in {total_time:.2f}s")
    logger.info(f"Time per shuffle: {time_per_shuffle:.4f}s")
    logger.info(f"Estimated time for 10,000 shuffles: {estimated_total_time:.2f}s")

    return result
