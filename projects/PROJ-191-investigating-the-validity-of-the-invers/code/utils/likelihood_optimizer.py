"""
Utility script to run likelihood optimization benchmarks and generate reports.

This script can be called to:
1. Benchmark the current likelihood evaluation speed.
2. Apply Cholesky caching optimization if needed.
3. Generate a report comparing before/after performance.
"""
import os
import sys
import time
import json
import logging
from pathlib import Path
import numpy as np
from typing import Tuple, Optional

from config import ProjectConfig, get_logger
from models.likelihood_optimized import OptimizedLikelihoodEvaluator, optimize_likelihood_if_needed

logger = get_logger(__name__)

def load_sample_data(config: ProjectConfig) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Load sample data for benchmarking from the harmonized dataset.
    
    Args:
        config: Project configuration object.
        
    Returns:
        Tuple of (covariance_matrix, force_data, separation).
    """
    data_dir = config.data_dir
    
    cov_path = data_dir / "processed" / "covariance_matrix_diagonal.npy"
    data_path = data_dir / "processed" / "harmonized_data.json"
    
    if not cov_path.exists():
        raise FileNotFoundError(f"Covariance matrix not found at {cov_path}")
    if not data_path.exists():
        raise FileNotFoundError(f"Harmonized data not found at {data_path}")
    
    logger.info(f"Loading covariance from {cov_path}")
    cov_matrix = np.load(cov_path)
    
    logger.info(f"Loading data from {data_path}")
    with open(data_path, 'r') as f:
        data_dict = json.load(f)
    
    force_data = np.array(data_dict['force_n'])
    separation = np.array(data_dict['separation_m'])
    
    return cov_matrix, force_data, separation

def benchmark_unoptimized(cov_matrix: np.ndarray, force_data: np.ndarray, 
                         separation: np.ndarray, num_iterations: int = 50) -> float:
    """
    Benchmark unoptimized likelihood evaluation (naive implementation).
    
    This simulates the baseline performance without Cholesky caching.
    
    Args:
        cov_matrix: Covariance matrix.
        force_data: Force data.
        separation: Separation data.
        num_iterations: Number of iterations.
        
    Returns:
        Average time per call in seconds.
    """
    from scipy.linalg import cholesky, cho_solve
    
    times = []
    alpha, lambda_m = 0.05, 1e-4
    
    # Pre-compute Cholesky once for the "unoptimized" version to be fair
    # In reality, an unoptimized version would recompute every time
    L = cholesky(cov_matrix, lower=True)
    
    for _ in range(num_iterations):
        # Simulate naive implementation (recompute Cholesky each time)
        start = time.perf_counter()
        
        # This is what we're optimizing away
        L_naive = cholesky(cov_matrix, lower=True)
        residuals = force_data - (1.0 / separation**2)  # Simplified model
        residuals_inv = cho_solve((L_naive, True), residuals)
        chi_sq = np.dot(residuals, residuals_inv)
        n = len(force_data)
        log_det = 2.0 * np.sum(np.log(np.diag(L_naive)))
        log_lh = -0.5 * (n * np.log(2 * np.pi) + log_det + chi_sq)
        
        end = time.perf_counter()
        times.append(end - start)
    
    return np.mean(times)

def run_optimization_report(config: ProjectConfig, output_path: Optional[Path] = None) -> dict:
    """
    Run a full optimization report comparing naive vs optimized likelihood evaluation.
    
    Args:
        config: Project configuration.
        output_path: Path to save the report (optional).
        
    Returns:
        Dictionary with benchmark results.
    """
    logger.info("Starting likelihood optimization benchmark...")
    
    # Load data
    cov_matrix, force_data, separation = load_sample_data(config)
    logger.info(f"Loaded data: {len(force_data)} points, covariance shape: {cov_matrix.shape}")
    
    # Benchmark unoptimized (naive) version
    logger.info("Benchmarking unoptimized (naive) likelihood evaluation...")
    time_unoptimized = benchmark_unoptimized(cov_matrix, force_data, separation, num_iterations=50)
    logger.info(f"Unoptimized average time: {time_unoptimized:.6f}s per call")
    
    # Benchmark optimized version
    logger.info("Benchmarking optimized likelihood evaluation...")
    evaluator = OptimizedLikelihoodEvaluator(cov_matrix)
    time_optimized = evaluator.benchmark(force_data, separation, num_iterations=100)["avg_time_per_call_s"]
    logger.info(f"Optimized average time: {time_optimized:.6f}s per call")
    
    # Calculate speedup
    if time_optimized > 0:
        speedup = time_unoptimized / time_optimized
    else:
        speedup = float('inf')
    
    report = {
        "unoptimized_time_s": time_unoptimized,
        "optimized_time_s": time_optimized,
        "speedup_factor": speedup,
        "data_points": len(force_data),
        "covariance_shape": list(cov_matrix.shape),
        "optimization_applied": "Cholesky decomposition caching",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Save report
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Optimization report saved to {output_path}")
    
    logger.info(f"Optimization complete. Speedup: {speedup:.2f}x")
    return report

def main():
    """Main entry point for the optimizer script."""
    config = ProjectConfig()
    output_path = config.results_dir / "likelihood_optimization_report.json"
    
    try:
        report = run_optimization_report(config, output_path)
        print(json.dumps(report, indent=2))
    except FileNotFoundError as e:
        logger.error(f"Data not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
