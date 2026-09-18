"""
Optimized bootstrap CI calculation using vectorized operations.

This module provides a high-performance implementation of the bootstrap
confidence interval calculation, replacing iterative Python loops with
vectorized NumPy operations for significant speed improvements.

The primary optimization is in the resampling step, which now uses
advanced indexing to generate all bootstrap samples simultaneously,
and the statistic calculation, which is vectorized across all samples.
"""
import os
import json
import csv
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass, asdict
import numpy as np
from scipy import stats

from code.config.env_config import get_path
from code.utils.random_seed import get_rng

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BootstrapResult:
    """Result of a bootstrap confidence interval calculation."""
    metric_name: str
    original_statistic: float
    bootstrap_mean: float
    ci_lower: float
    ci_upper: float
    p_value: float
    n_resamples: int
    computation_time_ms: float
    method: str

def calculate_bootstrap_ci_vectorized(
    baseline_values: List[float],
    post_values: List[float],
    n_resamples: int = 10000,
    confidence_level: float = 0.95,
    statistic_func: Optional[Callable[[np.ndarray, np.ndarray], float]] = None,
    rng: Optional[np.random.Generator] = None
) -> BootstrapResult:
    """
    Calculate bootstrap confidence interval using vectorized operations.
    
    This is the optimized version that replaces iterative resampling with
    vectorized NumPy operations. For 10,000 resamples, this is typically
    10-50x faster than the iterative version.
    
    Args:
        baseline_values: List of baseline measurement values
        post_values: List of post-intervention measurement values
        n_resamples: Number of bootstrap resamples (default: 10000)
        confidence_level: Confidence level for CI (default: 0.95)
        statistic_func: Optional custom statistic function. If None, uses 
                        mean difference (post - baseline).
        rng: NumPy random generator for reproducibility
    
    Returns:
        BootstrapResult with all calculated statistics
    
    Raises:
        ValueError: If input arrays are empty or have mismatched lengths
    """
    if not baseline_values or not post_values:
        raise ValueError("Input arrays cannot be empty")
    
    if len(baseline_values) != len(post_values):
        raise ValueError("Baseline and post arrays must have same length")
    
    baseline = np.array(baseline_values, dtype=np.float64)
    post = np.array(post_values, dtype=np.float64)
    n = len(baseline)
    
    if rng is None:
        rng = get_rng()
    
    start_time = time.perf_counter()
    
    # Vectorized resampling:
    # Generate all resample indices at once: shape (n_resamples, n)
    # Each row is a set of indices for one bootstrap sample
    resample_indices = rng.integers(0, n, size=(n_resamples, n))
    
    # Use advanced indexing to get all bootstrap samples at once
    # baseline_samples shape: (n_resamples, n)
    # post_samples shape: (n_resamples, n)
    baseline_samples = baseline[resample_indices]
    post_samples = post[resample_indices]
    
    # Calculate the statistic for all samples simultaneously
    # If using default (mean difference), this is fully vectorized
    if statistic_func is None:
        # Mean difference: mean(post) - mean(baseline)
        # Compute means across axis 1 (within each sample)
        baseline_means = np.mean(baseline_samples, axis=1)  # shape: (n_resamples,)
        post_means = np.mean(post_samples, axis=1)          # shape: (n_resamples,)
        bootstrap_stats = post_means - baseline_means        # shape: (n_resamples,)
    else:
        # For custom functions, we need to iterate but can still optimize
        # by batching if the function supports it
        bootstrap_stats = np.array([
            statistic_func(baseline_samples[i], post_samples[i])
            for i in range(n_resamples)
        ])
    
    # Calculate original statistic
    if statistic_func is None:
        original_statistic = float(np.mean(post) - np.mean(baseline))
    else:
        original_statistic = float(statistic_func(baseline, post))
    
    # Calculate bootstrap mean and confidence interval
    bootstrap_mean = float(np.mean(bootstrap_stats))
    
    # Percentile method for CI
    alpha = 1.0 - confidence_level
    ci_lower = float(np.percentile(bootstrap_stats, 100 * (alpha / 2)))
    ci_upper = float(np.percentile(bootstrap_stats, 100 * (1 - alpha / 2)))
    
    # Calculate p-value (two-tailed test: is original stat significantly different from 0?)
    # Count how many bootstrap samples are as extreme or more extreme than 0
    # Under null hypothesis, the distribution should be centered at 0
    # We test if the original statistic is in the tails of the bootstrap distribution
    if bootstrap_mean != 0:
        # Two-tailed p-value based on position in bootstrap distribution
        p_value = 2.0 * min(
            np.mean(bootstrap_stats <= original_statistic),
            np.mean(bootstrap_stats >= original_statistic)
        )
    else:
        p_value = 1.0
    
    computation_time_ms = (time.perf_counter() - start_time) * 1000
    
    return BootstrapResult(
        metric_name="mean_difference",
        original_statistic=original_statistic,
        bootstrap_mean=bootstrap_mean,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        p_value=p_value,
        n_resamples=n_resamples,
        computation_time_ms=computation_time_ms,
        method="percentile_vectorized"
    )

def run_bootstrap_analysis_optimized(
    data: Dict[str, List[float]],
    n_resamples: int = 10000,
    confidence_level: float = 0.95,
    output_path: Optional[str] = None
) -> Dict[str, BootstrapResult]:
    """
    Run optimized bootstrap analysis for multiple metrics.
    
    Args:
        data: Dictionary mapping metric names to (baseline, post) value lists
        n_resamples: Number of bootstrap resamples per metric
        confidence_level: Confidence level for CIs
        output_path: Optional path to write results JSON
    
    Returns:
        Dictionary mapping metric names to BootstrapResult objects
    """
    results = {}
    
    logger.info(f"Running optimized bootstrap analysis with {n_resamples} resamples")
    
    for metric_name, (baseline, post) in data.items():
        logger.info(f"Processing metric: {metric_name}")
        try:
            result = calculate_bootstrap_ci_vectorized(
                baseline_values=baseline,
                post_values=post,
                n_resamples=n_resamples,
                confidence_level=confidence_level
            )
            results[metric_name] = result
            logger.info(f"  Original stat: {result.original_statistic:.4f}, "
                        f"CI: [{result.ci_lower:.4f}, {result.ci_upper:.4f}], "
                        f"p={result.p_value:.4f}, time={result.computation_time_ms:.2f}ms")
        except Exception as e:
            logger.error(f"Error processing {metric_name}: {e}")
            raise
    
    # Write results if output path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert BootstrapResult to dict for JSON serialization
        serializable_results = {
            k: asdict(v) for k, v in results.items()
        }
        
        with open(output_path, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        logger.info(f"Results written to {output_path}")
    
    return results

def benchmark_performance(
    baseline_values: List[float],
    post_values: List[float],
    n_resamples: int = 10000,
    n_iterations: int = 5
) -> Dict[str, float]:
    """
    Benchmark the vectorized bootstrap implementation.
    
    Args:
        baseline_values: Baseline data
        post_values: Post data
        n_resamples: Number of resamples
        n_iterations: Number benchmark iterations
    
    Returns:
        Dictionary with timing statistics
    """
    times = []
    
    for i in range(n_iterations):
        start = time.perf_counter()
        calculate_bootstrap_ci_vectorized(
            baseline_values=baseline_values,
            post_values=post_values,
            n_resamples=n_resamples
        )
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    
    return {
        "mean_time_ms": float(np.mean(times)),
        "std_time_ms": float(np.std(times)),
        "min_time_ms": float(np.min(times)),
        "max_time_ms": float(np.max(times)),
        "n_resamples": n_resamples,
        "n_iterations": n_iterations
    }

def main():
    """Main entry point for the optimized bootstrap analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run optimized bootstrap confidence interval analysis"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/merged_data.csv",
        help="Path to merged data CSV"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/bootstrap_optimized_results.json",
        help="Path to output JSON file"
    )
    parser.add_argument(
        "--n-resamples",
        type=int,
        default=10000,
        help="Number of bootstrap resamples"
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run benchmark instead of full analysis"
    )
    
    args = parser.parse_args()
    
    if args.benchmark:
        # Run benchmark with sample data
        rng = get_rng()
        sample_baseline = rng.normal(loc=20, scale=5, size=50).tolist()
        sample_post = rng.normal(loc=18, scale=4, size=50).tolist()
        
        logger.info("Running benchmark...")
        bench_results = benchmark_performance(
            sample_baseline,
            sample_post,
            n_resamples=args.n_resamples
        )
        
        print("\n=== Performance Benchmark Results ===")
        print(f"Resamples: {bench_results['n_resamples']}")
        print(f"Iterations: {bench_results['n_iterations']}")
        print(f"Mean time: {bench_results['mean_time_ms']:.2f} ms")
        print(f"Std dev: {bench_results['std_time_ms']:.2f} ms")
        print(f"Min time: {bench_results['min_time_ms']:.2f} ms")
        print(f"Max time: {bench_results['max_time_ms']:.2f} ms")
        
        return bench_results
    
    # Full analysis
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return None
    
    # Load merged data
    data = {}
    with open(input_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Group by metric
    metrics = set()
    for row in rows:
        if 'metric_name' in row and 'value' in row and 'phase' in row:
            metrics.add(row['metric_name'])
    
    for metric in metrics:
        baseline_vals = []
        post_vals = []
        for row in rows:
            if row['metric_name'] == metric:
                val = float(row['value'])
                if row['phase'] == 'baseline':
                    baseline_vals.append(val)
                elif row['phase'] == 'post':
                    post_vals.append(val)
        
        if baseline_vals and post_vals:
            data[metric] = (baseline_vals, post_vals)
    
    if not data:
        logger.error("No valid data found in input file")
        return None
    
    logger.info(f"Found {len(data)} metrics to analyze")
    
    results = run_bootstrap_analysis_optimized(
        data=data,
        n_resamples=args.n_resamples,
        output_path=args.output
    )
    
    print("\n=== Optimized Bootstrap Analysis Results ===")
    for metric, result in results.items():
        print(f"\n{metric}:")
        print(f"  Original statistic: {result.original_statistic:.4f}")
        print(f"  Bootstrap mean: {result.bootstrap_mean:.4f}")
        print(f"  95% CI: [{result.ci_lower:.4f}, {result.ci_upper:.4f}]")
        print(f"  p-value: {result.p_value:.4f}")
        print(f"  Computation time: {result.computation_time_ms:.2f} ms")
        print(f"  Method: {result.method}")
    
    return results

if __name__ == "__main__":
    main()