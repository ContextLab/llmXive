"""
Utility functions for statistical modeling, including chunked permutation tests.
"""
import numpy as np
from typing import List, Tuple, Optional, Dict, Any, Callable
from joblib import Parallel, delayed
import json
import os
from scipy import stats
import logging

logger = logging.getLogger(__name__)


def benjamini_hochberg_fdr(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.

    Args:
        p_values: List of raw p-values.
        alpha: Significance level (default 0.05).

    Returns:
        List of adjusted q-values.
    """
    if not p_values:
        return []

    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array([p_values[i] for i in sorted_indices])

    # Calculate BH critical values
    ranks = np.arange(1, n + 1)
    critical_values = (ranks / n) * alpha

    # Find the largest k such that p(k) <= critical(k)
    # Then all p(i) for i <= k are significant
    # For q-values, we compute the minimum of (p_j * n / j) for j >= i
    q_values = np.zeros(n)
    current_min = 1.0
    for i in range(n - 1, -1, -1):
        q = sorted_p[i] * n / (i + 1)
        current_min = min(current_min, q)
        q_values[sorted_indices[i]] = current_min

    # Ensure q-values are monotonic and capped at 1.0
    q_values = np.minimum.accumulate(q_values[::-1])[::-1]
    q_values = np.clip(q_values, 0, 1)

    return q_values.tolist()


def bootstrap_confidence_interval(
    data: np.ndarray,
    statistic: Callable[[np.ndarray], float],
    n_bootstrap: int = 1000,
    alpha: float = 0.05,
    random_state: Optional[int] = None
) -> Tuple[float, float]:
    """
    Compute bootstrap confidence interval for a given statistic.

    Args:
        data: Input data array.
        statistic: Function to compute the statistic of interest.
        n_bootstrap: Number of bootstrap samples.
        alpha: Significance level (default 0.05 for 95% CI).
        random_state: Random seed for reproducibility.

    Returns:
        Tuple of (ci_lower, ci_upper).
    """
    if random_state is not None:
        np.random.seed(random_state)

    bootstrap_stats = []
    n = len(data)
    for _ in range(n_bootstrap):
        sample = np.random.choice(data, size=n, replace=True)
        bootstrap_stats.append(statistic(sample))

    lower_idx = int(alpha / 2 * n_bootstrap)
    upper_idx = int((1 - alpha / 2) * n_bootstrap)
    bootstrap_stats.sort()

    return bootstrap_stats[lower_idx], bootstrap_stats[upper_idx]


def run_permutation_chunked(
    data: np.ndarray,
    n_shuffles: int,
    chunk_size: int = 1000,
    statistic_func: Optional[Callable[[np.ndarray, np.ndarray], float]] = None,
    group_labels: Optional[np.ndarray] = None,
    random_state: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run permutation test in chunks to avoid memory overflow.

    This function splits the permutation shuffles into smaller batches,
    computing the test statistic for each chunk and aggregating results.

    Args:
        data: Input data array (or tuple of arrays if group_labels not provided).
        n_shuffles: Total number of permutation shuffles to perform.
        chunk_size: Number of shuffles per chunk (default 1000).
        statistic_func: Function that computes the test statistic.
                        If None, defaults to difference of means.
                        Signature: (group1, group2) -> float
        group_labels: Optional array of group labels (0 or 1). If None,
                      data is assumed to be a tuple of (group1, group2).
        random_state: Random seed for reproducibility.

    Returns:
        Dictionary with:
            - 'observed_stat': The test statistic on original data
            - 'p_value': Two-sided p-value from permutation test
            - 'n_shuffles': Total shuffles performed
            - 'null_distribution': List of all permutation statistics
    """
    if random_state is not None:
        np.random.seed(random_state)

    # Handle input formats
    if group_labels is None:
        if not isinstance(data, (tuple, list)) or len(data) != 2:
            raise ValueError("If group_labels is None, data must be a tuple of (group1, group2)")
        group1, group2 = data[0], data[1]
        combined = np.concatenate([group1, group2])
        n1, n2 = len(group1), len(group2)
    else:
        if len(data) != len(group_labels):
            raise ValueError("data and group_labels must have the same length")
        combined = np.array(data)
        n1 = np.sum(group_labels == 0)
        n2 = np.sum(group_labels == 1)

    # Default statistic function: difference of means
    if statistic_func is None:
        def statistic_func(g1, g2):
            return np.mean(g1) - np.mean(g2)

    # Compute observed statistic
    if group_labels is None:
        observed_stat = statistic_func(group1, group2)
    else:
        observed_stat = statistic_func(combined[group_labels == 0], combined[group_labels == 1])

    logger.info(f"Observed statistic: {observed_stat:.6f}")

    # Calculate number of chunks
    n_chunks = (n_shuffles + chunk_size - 1) // chunk_size
    if n_chunks * chunk_size > n_shuffles:
        # Adjust last chunk size
        pass  # We'll handle this in the loop

    null_stats = []
    total_shuffles = 0

    # Process in chunks
    for chunk_idx in range(n_chunks):
        current_chunk_size = min(chunk_size, n_shuffles - total_shuffles)
        chunk_stats = []

        for _ in range(current_chunk_size):
            # Permute combined data
            permuted = np.random.permutation(combined)

            # Split into groups
            if group_labels is None:
                p_group1 = permuted[:n1]
                p_group2 = permuted[n1:]
            else:
                p_group1 = permuted[group_labels == 0]
                p_group2 = permuted[group_labels == 1]

            # Compute statistic
            stat = statistic_func(p_group1, p_group2)
            chunk_stats.append(stat)

        null_stats.extend(chunk_stats)
        total_shuffles += current_chunk_size

        if (chunk_idx + 1) % 10 == 0 or total_shuffles >= n_shuffles:
            logger.info(f"Completed {total_shuffles}/{n_shuffles} shuffles")

    if total_shuffles != n_shuffles:
        raise RuntimeError(f"Expected {n_shuffles} shuffles, but only completed {total_shuffles}")

    # Calculate p-value (two-sided)
    abs_observed = abs(observed_stat)
    abs_null = np.abs(null_stats)
    p_value = np.sum(abs_null >= abs_observed) / n_shuffles

    logger.info(f"Permutation test complete. P-value: {p_value:.6f}")

    return {
        'observed_stat': float(observed_stat),
        'p_value': float(p_value),
        'n_shuffles': n_shuffles,
        'null_distribution': [float(x) for x in null_stats]
    }


def run_permutation_test(
    data: np.ndarray,
    n_shuffles: int,
    chunk_size: int = 1000,
    statistic_func: Optional[Callable[[np.ndarray, np.ndarray], float]] = None,
    group_labels: Optional[np.ndarray] = None,
    random_state: Optional[int] = None,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run permutation test with chunked processing and optional output saving.

    This is a wrapper around run_permutation_chunked that adds output handling.

    Args:
        data: Input data array.
        n_shuffles: Total number of permutation shuffles.
        chunk_size: Number of shuffles per chunk.
        statistic_func: Test statistic function.
        group_labels: Group labels array.
        random_state: Random seed.
        output_path: Optional path to save results as JSON.

    Returns:
        Dictionary with permutation test results.
    """
    result = run_permutation_chunked(
        data=data,
        n_shuffles=n_shuffles,
        chunk_size=chunk_size,
        statistic_func=statistic_func,
        group_labels=group_labels,
        random_state=random_state
    )

    if output_path:
        # Save results
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Results saved to {output_path}")

    return result


def save_permutation_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save permutation test results to a JSON file.

    Args:
        results: Dictionary containing permutation test results.
        output_path: Path to save the JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Permutation results saved to {output_path}")


def bootstrap_trajectory_confidence_intervals(
    trajectory_data: List[Dict[str, Any]],
    n_bootstrap: int = 1000,
    alpha: float = 0.05,
    random_state: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Compute bootstrap confidence intervals for trajectory shift magnitudes.

    Args:
        trajectory_data: List of trajectory shift results with 'shift_magnitude'.
        n_bootstrap: Number of bootstrap samples.
        alpha: Significance level.
        random_state: Random seed.

    Returns:
        List of results with added 'ci_lower' and 'ci_upper' fields.
    """
    if not trajectory_data:
        return []

    if random_state is not None:
        np.random.seed(random_state)

    # Extract shift magnitudes
    magnitudes = np.array([t['shift_magnitude'] for t in trajectory_data])
    n = len(magnitudes)

    # Bootstrap
    bootstrap_means = []
    for _ in range(n_bootstrap):
        sample = np.random.choice(magnitudes, size=n, replace=True)
        bootstrap_means.append(np.mean(sample))

    bootstrap_means.sort()
    lower_idx = int(alpha / 2 * n_bootstrap)
    upper_idx = int((1 - alpha / 2) * n_bootstrap)

    # Add CI to results
    results = []
    for t in trajectory_data:
        result = t.copy()
        result['ci_lower'] = float(bootstrap_means[lower_idx])
        result['ci_upper'] = float(bootstrap_means[upper_idx])
        results.append(result)

    return results
