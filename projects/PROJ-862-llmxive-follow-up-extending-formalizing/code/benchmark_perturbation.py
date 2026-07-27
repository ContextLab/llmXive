"""
Benchmark script to compare scalar vs. vectorized perturbation performance.

This script measures the runtime improvement of the vectorized implementation
over the original scalar loop, validating the optimization in T036.

Usage:
    python code/benchmark_perturbation.py
    
Output:
    Prints a comparison table of runtimes and throughput to stdout.
    Saves detailed results to data/processed/benchmark_results.json.
"""
import torch
import time
import json
import os
import logging
import numpy as np
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the optimized module
from perturbation_optimized import inject_and_project, inject_and_project_vectorized

# Import config to ensure paths are consistent
from config import load_config, OutputPaths
from memory_monitor import get_rss_memory_mb


def generate_synthetic_data(n_samples: int, dim: int, vocab_size: int) -> tuple:
    """
    Generate synthetic embeddings and model matrix for benchmarking.
    
    NOTE: This is ONLY for benchmarking the code path. The actual pipeline
    must use real data from the dataset loader.
    """
    logger.info(f"Generating synthetic benchmark data: {n_samples} samples, dim={dim}, vocab={vocab_size}")
    embeddings = torch.randn(n_samples, dim)
    model_matrix = torch.randn(vocab_size, dim)
    return embeddings, model_matrix


def run_benchmark(
    embeddings: torch.Tensor,
    model_matrix: torch.Tensor,
    sigma: float,
    name: str,
    func,
    iterations: int = 3
) -> Dict[str, Any]:
    """
    Run a benchmark for a specific function.
    """
    logger.info(f"Running benchmark: {name}")
    times = []
    results = None
    
    for i in range(iterations):
        start_time = time.perf_counter()
        # Warmup for first iteration if needed
        if i == 0:
            pass 
        
        ids, embs = func(embeddings, sigma, model_matrix)
        
        end_time = time.perf_counter()
        elapsed = end_time - start_time
        times.append(elapsed)
        
        # Verify correctness (shape check)
        assert ids.shape[0] == embeddings.shape[0], "ID shape mismatch"
        assert embs.shape[1] == embeddings.shape[1], "Emb shape mismatch"
    
    avg_time = np.mean(times)
    std_time = np.std(times)
    throughput = embeddings.shape[0] / avg_time
    
    logger.info(f"{name}: Avg time={avg_time:.4f}s, Std={std_time:.4f}s, Throughput={throughput:.1f} samples/s")
    
    return {
        "name": name,
        "avg_time_seconds": avg_time,
        "std_time_seconds": std_time,
        "throughput_samples_per_sec": throughput,
        "iterations": iterations
    }


def main():
    logger.info("Starting Perturbation Optimization Benchmark")
    
    # Configuration for benchmark
    # Using a realistic but manageable size for CPU benchmarking
    N_SAMPLES = 1000
    EMBED_DIM = 768  # Typical BERT/Llama hidden size
    VOCAB_SIZE = 30522 # Typical vocab size
    SIGMA = 0.5
    ITERATIONS = 5
    
    # Ensure output directory exists
    os.makedirs("data/processed", exist_ok=True)
    
    # Generate synthetic data for benchmarking
    embeddings, model_matrix = generate_synthetic_data(N_SAMPLES, EMBED_DIM, VOCAB_SIZE)
    
    # Ensure model matrix is on CPU
    embeddings = embeddings.cpu()
    model_matrix = model_matrix.cpu()
    
    results = []
    
    # Benchmark 1: Vectorized Implementation (Optimized)
    # We use the vectorized function directly to isolate the optimization
    vec_result = run_benchmark(
        embeddings, model_matrix, SIGMA, 
        "Vectorized (Optimized)", 
        lambda e, s, m: inject_and_project_vectorized(e, s, m, batch_size=512),
        iterations=ITERATIONS
    )
    results.append(vec_result)
    
    # Benchmark 2: Scalar Implementation (Baseline)
    # We explicitly disable vectorization to test the fallback loop
    scalar_result = run_benchmark(
        embeddings, model_matrix, SIGMA,
        "Scalar (Baseline)",
        lambda e, s, m: inject_and_project(e, s, m, use_vectorized=False),
        iterations=ITERATIONS
    )
    results.append(scalar_result)
    
    # Calculate improvement
    if scalar_result["avg_time_seconds"] > 0:
        speedup = scalar_result["avg_time_seconds"] / vec_result["avg_time_seconds"]
        logger.info(f"Speedup: {speedup:.2f}x")
        results.append({
            "name": "Speedup Factor",
            "value": speedup
        })
    else:
        logger.warning("Could not calculate speedup (scalar time was 0)")
    
    # Save results
    output_path = "data/processed/benchmark_results.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Benchmark results saved to {output_path}")
    
    # Print summary table
    print("\n" + "="*60)
    print("PERTURBATION OPTIMIZATION BENCHMARK RESULTS")
    print("="*60)
    print(f"{'Method':<30} {'Avg Time (s)':<15} {'Throughput':<20}")
    print("-"*60)
    for r in results:
        if r["name"] == "Speedup Factor":
            print(f"Speedup: {r['value']:.2f}x")
        else:
            print(f"{r['name']:<30} {r['avg_time_seconds']:<15.4f} {r['throughput_samples_per_sec']:<20.1f}")
    print("="*60)


if __name__ == "__main__":
    main()
