"""
Benchmark Runner for llmXive Project.

This script performs a profiling run of SVD and permutation loops on a
representative subset to verify the computational time constraint (SC-005).
It must fail the build if the projected runtime exceeds 6 hours.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
import torch

# Import project configuration
from config import (
    CONFIG_PATH,
    DATA_PROCESSED_DIR,
    DATA_RAW_DIR,
    PROJECT_ROOT,
    K,
    N_BOOTSTRAP,
    SEED,
)


def load_config() -> Dict[str, Any]:
    """Load configuration from config.py constants."""
    return {
        "k": K,
        "n_bootstrap": N_BOOTSTRAP,
        "seed": SEED,
        "max_runtime_hours": 6.0,
    }


def generate_synthetic_weights(vocab_size: int, embed_dim: int, seed: int) -> torch.Tensor:
    """
    Generate a synthetic unembedding matrix W_U for benchmarking.
    Uses a fixed seed for reproducibility.
    """
    torch.manual_seed(seed)
    # Initialize with standard normal distribution scaled by 1/sqrt(embed_dim)
    # to mimic typical transformer initialization
    std = 1.0 / np.sqrt(embed_dim)
    weights = torch.randn(vocab_size, embed_dim) * std
    return weights.float()


def benchmark_svd(weights: torch.Tensor, k: int, n_runs: int = 3) -> float:
    """
    Benchmark the time taken to compute top-k singular vectors.
    Returns the average time in seconds over n_runs.
    """
    times = []
    for _ in range(n_runs):
        start = time.perf_counter()
        # Compute top-k singular vectors using torch.svd or torch.linalg.svd
        # We only need the top-k, so we use torch.linalg.svd with full_matrices=False
        # and take the first k columns of U
        # Note: For very large matrices, randomized SVD might be faster, but we use standard SVD here for accuracy
        # Since we are on CPU, we ensure the tensor is on CPU
        u, s, vt = torch.linalg.svd(weights, full_matrices=False)
        # We only care about the time to compute, not the actual values for this benchmark
        # However, to prevent optimization, we touch the result
        _ = u[:, :k].sum()
        end = time.perf_counter()
        times.append(end - start)
    return sum(times) / n_runs


def benchmark_permutation(weights: torch.Tensor, k: int, n_iterations: int = 100) -> float:
    """
    Benchmark the time taken for a single iteration of the permutation test.
    This involves:
    1. Perturbing weights with Gaussian noise
    2. Running SVD on the perturbed weights
    3. Computing a similarity metric (cosine similarity of subspaces)

    Returns the average time per iteration in seconds.
    """
    times = []
    # We use a small subset for the benchmark to estimate per-iteration cost
    # The actual test will run N_BOOTSTRAP iterations
    for _ in range(n_iterations):
        start = time.perf_counter()
        # 1. Perturb weights: W_perturbed = W + noise
        noise = torch.randn_like(weights) * 0.01
        weights_perturbed = weights + noise

        # 2. Run SVD
        u_perturbed, s_perturbed, vt_perturbed = torch.linalg.svd(weights_perturbed, full_matrices=False)
        u_ref, s_ref, vt_ref = torch.linalg.svd(weights, full_matrices=False)

        # 3. Compute similarity (e.g., cosine similarity of the top-k subspaces)
        # We take the top-k columns of U
        u_perturbed_k = u_perturbed[:, :k]
        u_ref_k = u_ref[:, :k]

        # Normalize columns
        u_perturbed_k = u_perturbed_k / torch.norm(u_perturbed_k, dim=1, keepdim=True)
        u_ref_k = u_ref_k / torch.norm(u_ref_k, dim=1, keepdim=True)

        # Cosine similarity between subspaces (sum of dot products of corresponding vectors)
        similarity = torch.sum(torch.sum(u_perturbed_k * u_ref_k, dim=1))
        _ = similarity.item()  # Force computation

        end = time.perf_counter()
        times.append(end - start)

    return sum(times) / n_iterations


def project_runtime(svd_time: float, permutation_time: float, n_bootstrap: int) -> float:
    """
    Project the total runtime for the full experiment.
    The full experiment involves:
    1. One SVD per model (assume 3 models: Llama-3, Mistral, BLOOM)
    2. N_BOOTSTRAP iterations of the permutation test per model pair (3 pairs)

    Total time = 3 * svd_time + 3 * N_BOOTSTRAP * permutation_time
    """
    n_models = 3
    n_pairs = 3  # (Llama-Mistral, Llama-BLOOM, Mistral-BLOOM)
    total_time = n_models * svd_time + n_pairs * n_bootstrap * permutation_time
    return total_time


def run_benchmark(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Run the benchmark and return results.
    """
    config = load_config()
    k = config["k"]
    n_bootstrap = config["n_bootstrap"]
    max_runtime_hours = config["max_runtime_hours"]

    # Define representative dimensions (approximate for Llama-3/Mistral/BLOOM)
    # vocab_size ~ 32000, embed_dim ~ 4096 (for Llama-3 7B)
    # We use a slightly smaller dimension for the benchmark to keep it fast,
    # but large enough to be representative.
    # Let's use vocab_size=16000, embed_dim=2048 for the benchmark.
    # This is a 1/4 reduction in both dimensions, so the SVD will be roughly (1/4)^3 = 1/64 the time.
    # However, SVD is O(min(m*n^2, m^2*n)), so for m < n, it's O(m*n^2).
    # If we reduce both by 2, it's (1/2)^3 = 1/8.
    # To be safe, we'll use a more realistic size but still smaller than production.
    # Let's use vocab_size=8000, embed_dim=1024.
    vocab_size_benchmark = 8000
    embed_dim_benchmark = 1024

    print(f"Generating synthetic weights for benchmark: vocab_size={vocab_size_benchmark}, embed_dim={embed_dim_benchmark}")
    weights = generate_synthetic_weights(vocab_size_benchmark, embed_dim_benchmark, seed=config["seed"])

    print("Benchmarking SVD...")
    svd_time = benchmark_svd(weights, k)
    print(f"  Average SVD time: {svd_time:.4f} seconds")

    print("Benchmarking Permutation (100 iterations)...")
    permutation_time = benchmark_permutation(weights, k, n_iterations=100)
    print(f"  Average Permutation time per iteration: {permutation_time:.4f} seconds")

    # Project runtime for full experiment
    # We need to scale the benchmark times to the actual dimensions.
    # Let's assume the actual dimensions are:
    # vocab_size_actual = 32000, embed_dim_actual = 4096
    # The SVD time scales roughly as (embed_dim)^3 if vocab_size >= embed_dim (which is typical for LLMs)
    # But actually, for a matrix of shape (vocab_size, embed_dim), if vocab_size > embed_dim,
    # the complexity is O(vocab_size * embed_dim^2).
    # So the scaling factor for SVD is:
    # (vocab_size_actual * embed_dim_actual^2) / (vocab_size_benchmark * embed_dim_benchmark^2)
    svd_scale_factor = (32000 * 4096**2) / (vocab_size_benchmark * embed_dim_benchmark**2)
    svd_time_actual = svd_time * svd_scale_factor

    # For permutation, we do SVD on the perturbed matrix, so the same scaling applies.
    # But we also do the similarity calculation, which is O(vocab_size * k).
    # The similarity calculation is negligible compared to SVD, so we can ignore it for scaling.
    permutation_time_actual = permutation_time * svd_scale_factor

    total_runtime_seconds = project_runtime(svd_time_actual, permutation_time_actual, n_bootstrap)
    total_runtime_hours = total_runtime_seconds / 3600.0

    print(f"\nProjected Runtime for Full Experiment:")
    print(f"  SVD time (actual): {svd_time_actual:.2f} seconds")
    print(f"  Permutation time per iteration (actual): {permutation_time_actual:.2f} seconds")
    print(f"  Total projected runtime: {total_runtime_hours:.2f} hours ({total_runtime_seconds/3600*60:.2f} minutes)")

    # Check against constraint
    is_within_limit = total_runtime_hours <= max_runtime_hours
    status = "PASS" if is_within_limit else "FAIL"

    print(f"\nConstraint Check (SC-005): Max {max_runtime_hours} hours")
    print(f"  Status: {status}")

    # Save results
    results = {
        "benchmark_dimensions": {
            "vocab_size": vocab_size_benchmark,
            "embed_dim": embed_dim_benchmark,
        },
        "actual_dimensions": {
            "vocab_size": 32000,
            "embed_dim": 4096,
        },
        "scaling_factors": {
            "svd": svd_scale_factor,
        },
        "times_seconds": {
            "svd_benchmark": svd_time,
            "svd_actual": svd_time_actual,
            "permutation_iteration_benchmark": permutation_time,
            "permutation_iteration_actual": permutation_time_actual,
        },
        "projected_total_runtime_hours": total_runtime_hours,
        "max_runtime_hours": max_runtime_hours,
        "is_within_limit": is_within_limit,
        "status": status,
    }

    # Ensure output directory exists
    output_path = Path(DATA_PROCESSED_DIR) / "benchmark_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to {output_path}")

    if not is_within_limit:
        print("\nERROR: Projected runtime exceeds the 6-hour limit. The build must fail.")
        sys.exit(1)

    return results


def main():
    parser = argparse.ArgumentParser(description="Benchmark runner for llmXive project.")
    parser.add_argument("--config", type=str, default=None, help="Path to config file (not used, using config.py constants)")
    args = parser.parse_args()

    try:
        run_benchmark(args)
        print("\nBenchmark completed successfully.")
    except Exception as e:
        print(f"\nBenchmark failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()