"""
Benchmark Runner for Profiling SVD and Permutation Loops.

This module performs a profiling run on a representative subset (k=10 vocab)
to verify computational time constraints (SC-005). It projects the runtime
of the full operation based on the subset measurements.

Failure Threshold: Projected runtime > 5 hours causes the build to fail.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import numpy as np

# Local imports matching the API surface
from config import load_config, get_path, get_hyperparameter, get_seed
from model_analyzer import extract_svd_subspace, compute_cosine_similarity_subspaces

# Constants for the profiling subset
PROFILING_SUBSET_SIZE = 10  # k=10 vocab subset as per task description
FULL_SVD_K = 100            # Target k for full run
FULL_VOCAB_ESTIMATE = 50000 # Approximate vocab size for projection (conservative)
MAX_ALLOWED_HOURS = 5.0     # 5 hours threshold
MAX_ALLOWED_SECONDS = MAX_ALLOWED_HOURS * 3600


def load_config_wrapper() -> Dict[str, Any]:
    """Wrapper to load configuration safely."""
    try:
        return load_config()
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}


def generate_synthetic_weights(rows: int, cols: int, seed: int) -> np.ndarray:
    """
    Generate synthetic unembedding weights for profiling.
    Uses a fixed seed for reproducibility.
    """
    rng = np.random.default_rng(seed)
    # Simulate float32 unembedding matrix (Vocab x Hidden)
    # We use a smaller hidden dimension for the synthetic subset to speed up profiling
    # while maintaining the matrix shape ratio logic.
    hidden_dim = 4096 
    data = rng.normal(0, 0.02, (rows, hidden_dim)).astype(np.float32)
    return data


def benchmark_svd(matrix: np.ndarray, k: int, seed: int = 42) -> Tuple[float, Dict[str, Any]]:
    """
    Benchmarks the SVD extraction on a given matrix.
    
    Args:
        matrix: The unembedding matrix (Vocab x Hidden).
        k: Number of singular vectors to compute.
        seed: Random seed for reproducibility.
        
    Returns:
        Tuple of (elapsed_time_seconds, stats_dict)
    """
    rng = np.random.default_rng(seed)
    start_time = time.perf_counter()
    
    # Simulate the SVD operation on the subset
    # In a real run, this would call torch.svd or scipy.linalg.svd
    # We use numpy.linalg.svd for the profiling subset as it's CPU-bound
    # and sufficient for timing the linear algebra operation.
    try:
        # We only need the top-k singular vectors.
        # Using 'full_matrices=False' is critical for performance.
        # For the subset, we compute the full SVD of the small matrix.
        U, S, Vt = np.linalg.svd(matrix, full_matrices=False)
        top_k_vectors = U[:, :k]
    except Exception as e:
        end_time = time.perf_counter()
        return (end_time - start_time), {"error": str(e)}
    
    end_time = time.perf_counter()
    elapsed = end_time - start_time
    
    stats = {
        "matrix_shape": matrix.shape,
        "k_requested": k,
        "svd_time_seconds": elapsed,
        "memory_mb": (matrix.nbytes + U.nbytes + S.nbytes + Vt.nbytes) / (1024 * 1024)
    }
    
    return elapsed, stats


def benchmark_permutation(matrix: np.ndarray, n_iterations: int = 10, seed: int = 42) -> Tuple[float, Dict[str, Any]]:
    """
    Benchmarks the permutation loop (simulating the null distribution generation).
    
    Args:
        matrix: The unembedding matrix.
        n_iterations: Number of permutation iterations to simulate.
        seed: Random seed.
        
    Returns:
        Tuple of (elapsed_time_seconds, stats_dict)
    """
    rng = np.random.default_rng(seed)
    start_time = time.perf_counter()
    
    total_time = 0.0
    try:
        for i in range(n_iterations):
            # Simulate a permutation step: shuffle rows or apply random rotation
            # This is computationally cheaper than SVD but runs many times.
            # We simulate the cost of generating a null distribution.
            shuffled = rng.permutation(matrix)
            # Simulate a cheap similarity calculation
            _ = np.dot(shuffled.T, shuffled)
            total_time += time.perf_counter() - start_time # Approximate per-iteration cost
            start_time = time.perf_counter()
    except Exception as e:
        end_time = time.perf_counter()
        return (end_time - start_time), {"error": str(e)}
    
    end_time = time.perf_counter()
    elapsed = end_time - start_time
    
    stats = {
        "matrix_shape": matrix.shape,
        "iterations": n_iterations,
        "permutation_time_seconds": elapsed,
    }
    
    return elapsed, stats


def project_runtime(subset_svd_time: float, subset_perm_time: float) -> Dict[str, float]:
    """
    Projects the runtime for the full dataset based on the subset measurements.
    
    Assumptions:
    - SVD complexity is roughly O(V * H^2) or O(V * H * k) depending on implementation.
      We assume linear scaling with respect to Vocab size (V) for the subset vs full.
    - Permutation loop scales linearly with iterations and matrix operations.
    
    Args:
        subset_svd_time: Time taken for the subset SVD.
        subset_perm_time: Time taken for the subset permutation loop.
        
    Returns:
        Dictionary with projected times.
    """
    # Scaling factor: Full Vocab Estimate / Profiling Subset Size
    # We assume the hidden dimension and k remain constant.
    scaling_factor = FULL_VOCAB_ESTIMATE / PROFILING_SUBSET_SIZE
    
    # Projected SVD time (linear scaling with vocab size for subset)
    projected_svd = subset_svd_time * scaling_factor
    
    # Projected Permutation time (assuming we run enough iterations for convergence)
    # If the subset ran 10 iterations, the full run might need 1000.
    # We assume the permutation loop is dominated by the number of iterations.
    # Let's assume a standard full run needs 1000 iterations.
    full_iterations = 1000
    subset_iterations = 10
    iter_scaling = full_iterations / subset_iterations
    
    projected_perm = subset_perm_time * scaling_factor * iter_scaling
    
    total_projected = projected_svd + projected_perm
    
    return {
        "projected_svd_hours": projected_svd / 3600,
        "projected_perm_hours": projected_perm / 3600,
        "total_projected_hours": total_projected / 3600,
        "scaling_factor_vocab": scaling_factor,
        "iterations_scaled": iter_scaling
    }


def run_benchmark(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes the benchmark profiling run.
    
    Returns:
        Dictionary containing benchmark results and pass/fail status.
    """
    seed = get_seed()
    k = get_hyperparameter("k", 100)
    
    print(f"Starting benchmark with seed={seed}, k={k}")
    print(f"Profiling subset size: {PROFILING_SUBSET_SIZE}")
    
    # 1. Generate Synthetic Subset
    # Note: This is synthetic ONLY for the PURPOSE of profiling the algorithm's
    # computational complexity on a representative matrix shape. 
    # The actual data loading happens in the real pipeline.
    # We simulate the shape of the unembedding matrix for the subset.
    print("Generating synthetic subset matrix...")
    # Shape: (Profiling_Vocab_Size, Hidden_Dim)
    # We use a representative hidden dim (e.g., 4096)
    synthetic_matrix = generate_synthetic_weights(PROFILING_SUBSET_SIZE, 4096, seed)
    
    # 2. Benchmark SVD
    print("Running SVD benchmark on subset...")
    svd_time, svd_stats = benchmark_svd(synthetic_matrix, k, seed)
    print(f"SVD subset time: {svd_time:.4f}s")
    
    # 3. Benchmark Permutation
    print("Running Permutation benchmark on subset...")
    perm_time, perm_stats = benchmark_permutation(synthetic_matrix, n_iterations=10, seed=seed)
    print(f"Permutation subset time: {perm_time:.4f}s")
    
    # 4. Project Runtime
    projections = project_runtime(svd_time, perm_time)
    print(f"Projected Total Runtime: {projections['total_projected_hours']:.2f} hours")
    
    # 5. Check Threshold
    passed = projections['total_projected_hours'] <= MAX_ALLOWED_HOURS
    status = "PASS" if passed else "FAIL"
    
    result = {
        "status": status,
        "threshold_hours": MAX_ALLOWED_HOURS,
        "projected_hours": projections['total_projected_hours'],
        "subset_results": {
            "svd": svd_stats,
            "permutation": perm_stats
        },
        "projections": projections,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return result


def main():
    """Main entry point for the benchmark runner."""
    parser = argparse.ArgumentParser(description="Profile SVD and Permutation runtime")
    parser.add_argument("--config", type=str, default="config.json", help="Path to config file")
    parser.add_argument("--output", type=str, default="data/processed/benchmark_report.json", 
                        help="Path to output report")
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load config
    config = load_config_wrapper()
    if not config:
        # Fallback if config loading fails, use defaults
        config = {}
    
    # Run benchmark
    result = run_benchmark(config)
    
    # Save result
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"Report saved to {output_path}")
    
    # Exit with error code if failed
    if result["status"] == "FAIL":
        print(f"BENCHMARK FAILED: Projected runtime ({result['projected_hours']:.2f}h) exceeds threshold ({result['threshold_hours']}h).")
        sys.exit(1)
    else:
        print("BENCHMARK PASSED: Projected runtime is within limits.")
        sys.exit(0)


if __name__ == "__main__":
    main()
