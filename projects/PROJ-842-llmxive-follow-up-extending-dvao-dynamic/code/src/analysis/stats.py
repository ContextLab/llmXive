"""
Statistical analysis utilities for DVAO.

Implements batched variance calculations to reduce memory footprint,
along with various statistical tests and validation routines.
"""
import numpy as np
from typing import List, Dict, Tuple, Optional, Union, Generator, Any
from scipy import stats
import warnings
import psutil
import os
import json
from collections import deque
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_memory_usage_bytes() -> int:
    """
    Get current memory usage of the process in bytes.
    
    Returns:
        int: Memory usage in bytes
    """
    process = psutil.Process(os.getpid())
    return process.memory_info().rss


def check_memory_limit(limit_gb: float = 7.0) -> None:
    """
    Check if current memory usage exceeds the specified limit.
    
    Args:
        limit_gb: Memory limit in gigabytes (default 7.0)
        
    Raises:
        MemoryError: If memory usage exceeds the limit
    """
    current_bytes = get_memory_usage_bytes()
    limit_bytes = limit_gb * 1024 ** 3
    if current_bytes > limit_bytes:
        raise MemoryError(
            f"Memory usage {current_bytes / (1024**3):.2f}GB exceeds limit {limit_gb}GB"
        )
    logger.info(f"Memory check passed: {current_bytes / (1024**3):.2f}GB < {limit_gb}GB")


def batched_variance_generator(
    data_stream: Generator[np.ndarray, None, None],
    batch_size: int = 1000,
    memory_check_interval: int = 100
) -> Generator[Tuple[int, float], None, None]:
    """
    Generator that processes data in batches to calculate variance while
    monitoring memory usage.
    
    This is the core memory-efficient implementation for T055.
    
    Args:
        data_stream: Generator yielding numpy arrays of data points
        batch_size: Number of samples to process per batch
        memory_check_interval: Check memory every N batches
        
    Yields:
        Tuple of (batch_index, batch_variance)
    """
    batch_count = 0
    total_samples = 0
    
    for batch_idx, batch_data in enumerate(data_stream):
        if batch_data.size == 0:
            continue
            
        # Calculate variance for this batch
        batch_var = np.var(batch_data, ddof=1)
        total_samples += batch_data.size
        
        yield batch_idx, batch_var
        batch_count += 1
        
        # Periodic memory check
        if batch_count % memory_check_interval == 0:
            check_memory_limit()
    
    logger.info(f"Processed {batch_count} batches, {total_samples} total samples")


def calculate_batched_variance(
    data: np.ndarray,
    batch_size: int = 10000
) -> Tuple[float, int]:
    """
    Calculate variance of large arrays using batch processing to reduce
    peak memory usage.
    
    Uses Welford's online algorithm for numerical stability.
    
    Args:
        data: Input data array (can be very large)
        batch_size: Number of elements to process per batch
        
    Returns:
        Tuple of (variance, sample_count)
    """
    n = 0
    mean = 0.0
    M2 = 0.0
    
    total_elements = data.size
    num_batches = (total_elements + batch_size - 1) // batch_size
    
    logger.info(f"Calculating variance in {num_batches} batches for {total_elements} elements")
    
    for batch_idx in range(num_batches):
        start_idx = batch_idx * batch_size
        end_idx = min((batch_idx + 1) * batch_size, total_elements)
        
        # Reshape for batch processing if needed
        batch = data[start_idx:end_idx]
        
        # Welford's online algorithm
        for x in batch:
            n += 1
            delta = x - mean
            mean += delta / n
            delta2 = x - mean
            M2 += delta * delta2
        
        # Periodic memory check
        if (batch_idx + 1) % 10 == 0:
            check_memory_limit()
    
    variance = M2 / (n - 1) if n > 1 else 0.0
    logger.info(f"Batched variance calculation complete: {variance:.6f} from {n} samples")
    return variance, n


def paired_ttest_heuristic_vs_fullbatch(
    heuristic_vals: np.ndarray,
    fullbatch_vals: np.ndarray
) -> Dict[str, float]:
    """
    Perform paired t-test comparing heuristic variance vs full-batch empirical variance.
    
    Args:
        heuristic_vals: Array of variance estimates from heuristic method
        fullbatch_vals: Array of variance estimates from full-batch method
        
    Returns:
        Dictionary with 't_statistic' and 'p_value'
    """
    if len(heuristic_vals) != len(fullbatch_vals):
        raise ValueError("Input arrays must have the same length for paired t-test")
    
    t_stat, p_val = stats.ttest_rel(heuristic_vals, fullbatch_vals)
    
    logger.info(f"Paired t-test: t={t_stat:.4f}, p={p_val:.4f}")
    return {
        't_statistic': float(t_stat),
        'p_value': float(p_val)
    }


def check_stability(
    heuristic_vals: np.ndarray,
    fullbatch_vals: np.ndarray,
    tolerance: float = 0.1,
    threshold_ratio: float = 0.95
) -> Dict[str, Any]:
    """
    Check if the ratio of heuristic to full-batch variance remains stable.
    
    Args:
        heuristic_vals: Heuristic variance estimates
        fullbatch_vals: Full-batch variance estimates
        tolerance: Allowed deviation from 1.0 (e.g., 0.1 for [0.9, 1.1])
        threshold_ratio: Minimum fraction of points that must be within tolerance
        
    Returns:
        Dictionary with stability metrics
    """
    if len(heuristic_vals) != len(fullbatch_vals):
        raise ValueError("Input arrays must have the same length")
    
    # Avoid division by zero
    with np.errstate(divide='ignore', invalid='ignore'):
        ratios = heuristic_vals / fullbatch_vals
    
    # Filter out invalid ratios
    valid_mask = np.isfinite(ratios)
    valid_ratios = ratios[valid_mask]
    
    if len(valid_ratios) == 0:
        return {
            'stable': False,
            'ratio_mean': None,
            'ratio_std': None,
            'within_tolerance_ratio': 0.0,
            'message': 'No valid ratios computed'
        }
    
    within_tolerance = np.abs(valid_ratios - 1.0) <= tolerance
    within_tolerance_ratio = np.mean(within_tolerance)
    
    stable = within_tolerance_ratio >= threshold_ratio
    
    result = {
        'stable': bool(stable),
        'ratio_mean': float(np.mean(valid_ratios)),
        'ratio_std': float(np.std(valid_ratios)),
        'within_tolerance_ratio': float(within_tolerance_ratio),
        'tolerance': tolerance,
        'threshold_ratio': threshold_ratio
    }
    
    logger.info(f"Stability check: {result['within_tolerance_ratio']:.2%} within [{1-tolerance}, {1+tolerance}]")
    return result


def run_sensitivity_analysis(
    data: np.ndarray,
    window_sizes: List[int]
) -> Dict[int, float]:
    """
    Run sensitivity analysis on different window sizes for variance estimation.
    
    Args:
        data: Input data array
        window_sizes: List of window sizes to test
        
    Returns:
        Dictionary mapping window size to estimated variance
    """
    results = {}
    
    for k in window_sizes:
        if k >= len(data):
            warnings.warn(f"Window size {k} >= data length {len(data)}, skipping")
            continue
        
        # Use last k steps for variance estimation
        window_data = data[-k:]
        variance = np.var(window_data, ddof=1)
        results[k] = float(variance)
        
        logger.debug(f"Window size {k}: variance = {variance:.6f}")
    
    return results


def calculate_correlation_variance_error_pareto(
    variance_errors: np.ndarray,
    pareto_distances: np.ndarray
) -> Dict[str, float]:
    """
    Calculate correlation between variance estimation error and distance to Pareto frontier.
    
    Args:
        variance_errors: Array of variance estimation errors
        pareto_distances: Array of distances to Pareto frontier
        
    Returns:
        Dictionary with Pearson and Spearman correlation coefficients
    """
    if len(variance_errors) != len(pareto_distances):
        raise ValueError("Input arrays must have the same length")
    
    # Pearson correlation
    pearson_r, pearson_p = stats.pearsonr(variance_errors, pareto_distances)
    
    # Spearman correlation
    spearman_r, spearman_p = stats.spearmanr(variance_errors, pareto_distances)
    
    logger.info(f"Correlation: Pearson={pearson_r:.4f} (p={pearson_p:.4f}), "
               f"Spearman={spearman_r:.4f} (p={spearman_p:.4f})")
    
    return {
        'pearson_correlation': float(pearson_r),
        'pearson_p_value': float(pearson_p),
        'spearman_correlation': float(spearman_r),
        'spearman_p_value': float(spearman_p)
    }


def run_one_sample_ttest(
    sample: np.ndarray,
    theoretical_mean: float
) -> Dict[str, float]:
    """
    Perform one-sample t-test comparing sample mean to theoretical bound.
    
    Args:
        sample: Array of sample values
        theoretical_mean: Theoretical mean to test against
        
    Returns:
        Dictionary with t-statistic and p-value
    """
    t_stat, p_val = stats.ttest_1samp(sample, theoretical_mean)
    
    logger.info(f"One-sample t-test vs {theoretical_mean}: t={t_stat:.4f}, p={p_val:.4f}")
    return {
        't_statistic': float(t_stat),
        'p_value': float(p_val),
        'sample_mean': float(np.mean(sample)),
        'theoretical_mean': theoretical_mean
    }


def run_noise_sanity_check(
    empirical_variance: float,
    theoretical_sigma_sq: float,
    tolerance: float = 0.2
) -> Dict[str, Any]:
    """
    Sanity check to verify empirical noise matches theoretical sigma^2.
    
    Args:
        empirical_variance: Observed variance from data
        theoretical_sigma_sq: Theoretical noise variance
        tolerance: Allowed relative deviation
        
    Returns:
        Dictionary with check result and deviation metric
    """
    if theoretical_sigma_sq == 0:
        return {
            'passed': False,
            'deviation': float('inf'),
            'message': 'Theoretical variance is zero'
        }
    
    deviation = abs(empirical_variance - theoretical_sigma_sq) / theoretical_sigma_sq
    passed = deviation <= tolerance
    
    logger.info(f"Noise sanity check: deviation={deviation:.2%}, passed={passed}")
    return {
        'passed': bool(passed),
        'deviation': float(deviation),
        'empirical_variance': float(empirical_variance),
        'theoretical_sigma_sq': float(theoretical_sigma_sq),
        'tolerance': tolerance
    }


def run_stability_check(
    heuristic_vals: np.ndarray,
    fullbatch_vals: np.ndarray,
    tolerance: float = 0.1,
    threshold_ratio: float = 0.95
) -> Dict[str, Any]:
    """
    Verify ratio of heuristic to full-batch variance remains within [0.9, 1.1]
    for at least 95% of steps.
    
    Args:
        heuristic_vals: Heuristic variance estimates
        fullbatch_vals: Full-batch variance estimates
        tolerance: Allowed deviation from 1.0
        threshold_ratio: Minimum fraction of points within tolerance
        
    Returns:
        Dictionary with stability metrics
    """
    return check_stability(heuristic_vals, fullbatch_vals, tolerance, threshold_ratio)


def run_sensitivity_sweep(
    data: np.ndarray,
    window_sizes: List[int],
    batch_size: int = 10000
) -> Dict[str, Any]:
    """
    Run sensitivity analysis sweep over window sizes with batch processing.
    
    Args:
        data: Input data array
        window_sizes: List of window sizes to test
        batch_size: Batch size for memory-efficient processing
        
    Returns:
        Dictionary with sweep results and metadata
    """
    results = {}
    
    for k in window_sizes:
        if k >= len(data):
            logger.warning(f"Window size {k} >= data length {len(data)}, skipping")
            continue
        
        # Use batched variance calculation for memory efficiency
        window_data = data[-k:]
        variance, n = calculate_batched_variance(window_data, batch_size=batch_size)
        results[str(k)] = {
            'variance': variance,
            'n_samples': n
        }
        
        check_memory_limit()
    
    return {
        'window_sizes_tested': window_sizes,
        'results': results,
        'total_window_sizes': len(results)
    }


def calculate_windowed_variance_batched(
    data: np.ndarray,
    window_size: int,
    batch_size: int = 10000
) -> float:
    """
    Calculate windowed variance using batch processing for memory efficiency.
    
    Args:
        data: Input data array
        window_size: Size of the sliding window
        batch_size: Batch size for processing
        
    Returns:
        Variance estimate from the last window
    """
    if window_size >= len(data):
        raise ValueError(f"Window size {window_size} must be less than data length {len(data)}")
    
    # Extract the last window
    window_data = data[-window_size:]
    
    # Use batched variance calculation
    variance, n = calculate_batched_variance(window_data, batch_size)
    
    return variance


def validate_heavy_tailed_pareto(
    pareto_distances: np.ndarray,
    threshold: float = 0.1
) -> Dict[str, Any]:
    """
    Validate heavy-tailed noise distribution against Pareto distance threshold.
    
    Args:
        pareto_distances: Array of distances to Pareto frontier
        threshold: Maximum allowed deviation (default 0.1 for 10%)
        
    Returns:
        Dictionary with validation results
    """
    mean_distance = np.mean(pareto_distances)
    threshold_passed = mean_distance <= threshold
    
    logger.info(f"Heavy-tailed validation: mean_distance={mean_distance:.4f}, "
               f"threshold={threshold}, passed={threshold_passed}")
    
    return {
        'mean_distance': float(mean_distance),
        'threshold': float(threshold),
        'threshold_passed': bool(threshold_passed),
        'std_distance': float(np.std(pareto_distances)),
        'n_samples': len(pareto_distances)
    }


def validate_heavy_tailed(
    empirical_results: np.ndarray,
    theoretical_bound: float,
    threshold: float = 0.1
) -> Dict[str, Any]:
    """
    Compare heavy-tailed held-out set results against theoretical bound.
    
    Args:
        empirical_results: Array of empirical measurements
        theoretical_bound: Theoretical bound to compare against
        threshold: Maximum allowed deviation (default 0.1 for 10%)
        
    Returns:
        Dictionary with validation results
    """
    mean_result = np.mean(empirical_results)
    deviation = abs(mean_result - theoretical_bound) / theoretical_bound if theoretical_bound != 0 else float('inf')
    threshold_passed = deviation <= threshold
    
    logger.info(f"Heavy-tailed comparison: mean={mean_result:.4f}, "
               f"bound={theoretical_bound}, deviation={deviation:.2%}, passed={threshold_passed}")
    
    return {
        'mean_empirical': float(mean_result),
        'theoretical_bound': float(theoretical_bound),
        'deviation': float(deviation),
        'threshold': float(threshold),
        'threshold_passed': bool(threshold_passed),
        'n_samples': len(empirical_results)
    }


def main():
    """
    CLI entry point for running batched variance calculations and memory checks.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Batched variance analysis with memory monitoring')
    parser.add_argument('--batch-size', type=int, default=10000, help='Batch size for processing')
    parser.add_argument('--limit-gb', type=float, default=7.0, help='Memory limit in GB')
    parser.add_argument('--test-memory', action='store_true', help='Run memory limit test')
    
    args = parser.parse_args()
    
    logger.info(f"Starting batched variance analysis with batch_size={args.batch_size}, limit={args.limit_gb}GB")
    
    if args.test_memory:
        # Generate test data and check memory
        try:
            logger.info("Running memory test...")
            check_memory_limit(args.limit_gb)
            logger.info("Memory test passed")
        except MemoryError as e:
            logger.error(f"Memory test failed: {e}")
            return 1
    
    logger.info("Batched variance analysis module loaded successfully")
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
