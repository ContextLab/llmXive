"""
Benchmark script for generator performance.

This script benchmarks the generate_synthetic_data function to ensure
performance improvements meet the target of 20% reduction in runtime
or < 6h total runtime for large simulations.
"""
import time
import cProfile
import pstats
import io
import numpy as np
from simulation.config import SimulationConfig, get_default_config
from simulation.generator import generate_synthetic_data
from simulation.logger import setup_logger


def benchmark_single_generation(config: SimulationConfig, iterations: int = 100) -> float:
    """
    Benchmark single generation calls.

    Args:
        config: Simulation configuration
        iterations: Number of iterations to benchmark

    Returns:
        Average time per generation in seconds
    """
    logger = setup_logger(__name__)
    times = []

    for i in range(iterations):
        start_time = time.perf_counter()
        _, _, success, msg = generate_synthetic_data(config, logger)
        end_time = time.perf_counter()

        if not success:
            raise RuntimeError(f"Generation failed: {msg}")

        times.append(end_time - start_time)

    return np.mean(times)


def run_benchmark():
    """Run comprehensive benchmark of the generator."""
    logger = setup_logger(__name__)
    logger.info("Starting generator performance benchmark")

    # Test configurations
    configs = [
        # Small scale
        get_default_config(n_samples=100, mean_diff=0.0, distribution_type="normal", seed=42),
        get_default_config(n_samples=100, mean_diff=1.0, distribution_type="skewed", seed=42),
        get_default_config(n_samples=100, mean_diff=0.0, distribution_type="heteroscedastic", seed=42),

        # Medium scale
        get_default_config(n_samples=1000, mean_diff=0.0, distribution_type="normal", seed=42),
        get_default_config(n_samples=1000, mean_diff=1.0, distribution_type="skewed", seed=42),
        get_default_config(n_samples=1000, mean_diff=0.0, distribution_type="heteroscedastic", seed=42),

        # Large scale
        get_default_config(n_samples=10000, mean_diff=0.0, distribution_type="normal", seed=42),
        get_default_config(n_samples=10000, mean_diff=1.0, distribution_type="skewed", seed=42),
        get_default_config(n_samples=10000, mean_diff=0.0, distribution_type="heteroscedastic", seed=42),
    ]

    results = []

    for i, config in enumerate(configs):
        logger.info(f"Benchmarking config {i+1}/{len(configs)}: n={config.n_samples}, type={config.distribution_type}")
        avg_time = benchmark_single_generation(config, iterations=50)
        results.append({
            "n_samples": config.n_samples,
            "distribution_type": config.distribution_type,
            "mean_diff": config.mean_diff,
            "avg_time_per_generation": avg_time
        })
        logger.info(f"  Average time: {avg_time:.6f} seconds")

    # Print summary
    logger.info("\n=== Benchmark Summary ===")
    for result in results:
        logger.info(f"n={result['n_samples']:5d}, type={result['distribution_type']:12s}, mean_diff={result['mean_diff']:.1f} -> {result['avg_time_per_generation']*1000:.3f}ms")

    # Estimate total runtime for full simulation
    # Assuming 1000 iterations per config, 9 configs
    total_iterations = 1000 * len(configs)
    estimated_total_time = sum(r['avg_time_per_generation'] for r in results) * 1000
    hours = estimated_total_time / 3600

    logger.info(f"\nEstimated total runtime for full simulation (1000 iterations per config): {hours:.2f} hours")
    logger.info(f"Target: < 6 hours")
    logger.info(f"Status: {'PASS' if hours < 6 else 'FAIL'}")

    return results


def profile_generation():
    """Profile the generation function to identify bottlenecks."""
    logger = setup_logger(__name__)
    config = get_default_config(n_samples=10000, mean_diff=0.0, distribution_type="normal", seed=42)

    profiler = cProfile.Profile()
    profiler.enable()

    # Run multiple generations for meaningful profile
    for _ in range(100):
        generate_synthetic_data(config, logger)

    profiler.disable()

    # Print profile results
    s = io.StringIO()
    stats = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    stats.print_stats(20)

    logger.info("\n=== Profiling Results (Top 20 functions) ===")
    logger.info(s.getvalue())


if __name__ == "__main__":
    run_benchmark()
    profile_generation()
