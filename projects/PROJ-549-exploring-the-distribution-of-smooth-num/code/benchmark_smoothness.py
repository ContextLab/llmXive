import argparse
import json
import logging
import os
import sys
import time
from typing import Dict, Any, List, Tuple

import numpy as np

# Import from existing modules based on API surface
from smoothness import load_primes_from_csv, is_y_smooth, count_smooth_in_interval, setup_logging
from smoothness_vectorized import load_primes_as_array, is_y_smooth_vectorized, count_smooth_in_interval_vectorized
from config import load_config, GridConfig

def run_benchmark(
    primes_baseline: List[int],
    primes_vectorized: np.ndarray,
    x: int,
    y: int,
    h: int,
    iterations: int = 5
) -> Dict[str, float]:
    """
    Runs the baseline (loop) and vectorized (numpy) smoothness counters
    over the same interval [x, x+h] for a given y-smoothness bound.
    """
    # Baseline timing
    baseline_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        # Run the baseline function
        count_smooth_in_interval(primes_baseline, x, y, h)
        end = time.perf_counter()
        baseline_times.append((end - start) * 1000)  # Convert to ms

    baseline_ms = sum(baseline_times) / len(baseline_times)

    # Vectorized timing
    optimized_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        # Run the vectorized function
        count_smooth_in_interval_vectorized(primes_vectorized, x, y, h)
        end = time.perf_counter()
        optimized_times.append((end - start) * 1000)  # Convert to ms

    optimized_ms = sum(optimized_times) / len(optimized_times)

    speedup = baseline_ms / optimized_ms if optimized_ms > 0 else float('inf')

    return {
        "baseline_ms": round(baseline_ms, 3),
        "optimized_ms": round(optimized_ms, 3),
        "speedup_factor": round(speedup, 2)
    }

def main():
    args = parse_args()
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    # Load configuration to get parameters
    config = load_config()
    # Use a representative configuration from the grid for benchmarking
    # We select a moderate x and y to ensure the benchmark is meaningful but not too long
    x = config.grid_config.x_list[1] if len(config.grid_config.x_list) > 1 else 10**7
    y = config.grid_config.y_list[0]
    h = 10000  # Fixed interval length for benchmark consistency

    logger.info(f"Running benchmark for interval [{x}, {x+h}], y={y}")

    # Load primes for baseline
    logger.info("Loading primes for baseline...")
    try:
        primes_baseline = load_primes_from_csv("data/primes_1e9.csv")
    except FileNotFoundError:
        logger.error("data/primes_1e9.csv not found. Please run T012/T013 first.")
        sys.exit(1)

    # Load primes for vectorized (as array)
    logger.info("Loading primes for vectorized analysis...")
    try:
        primes_vectorized = load_primes_as_array("data/primes_1e9.csv")
    except FileNotFoundError:
        logger.error("data/primes_1e9.csv not found. Please run T012/T013 first.")
        sys.exit(1)

    # Run benchmark
    logger.info("Starting benchmark...")
    results = run_benchmark(primes_baseline, primes_vectorized, x, y, h, iterations=5)

    # Determine pass/fail based on speedup (expecting optimization to be faster or at least not significantly slower)
    # We define 'passed' as speedup >= 0.8 (optimized is at least 80% as fast as baseline, allowing for overhead)
    # Ideally, we expect speedup > 1.0
    passed = results["speedup_factor"] >= 0.8

    results["passed"] = passed

    # Save results
    output_path = "data/benchmark_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Benchmark complete. Results saved to {output_path}")
    logger.info(f"Baseline: {results['baseline_ms']}ms, Optimized: {results['optimized_ms']}ms, Speedup: {results['speedup_factor']}x")
    logger.info(f"Test {'PASSED' if passed else 'FAILED'}: Speedup factor is {results['speedup_factor']}")

    if not passed:
        logger.warning("Optimized version was significantly slower than baseline. Check implementation.")
        sys.exit(1)

def parse_args():
    parser = argparse.ArgumentParser(description="Benchmark smoothness analysis implementations")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    return parser.parse_args()

if __name__ == "__main__":
    main()
