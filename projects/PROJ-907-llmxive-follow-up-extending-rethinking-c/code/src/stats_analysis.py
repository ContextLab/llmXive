import json
import logging
import os
import sys
import subprocess
import shutil
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_benchmark_with_seed(seed: int) -> Dict[str, float]:
    """Runs the benchmark with a specific seed and returns the results."""
    # Placeholder for actual benchmark logic
    return {
        "static_fid": 10.5,
        "dynamic_fid": 10.0
    }

def compute_paired_difference_stats(static_fids: List[float], dynamic_fids: List[float]) -> Dict[str, float]:
    """Computes paired difference statistics."""
    if len(static_fids) != len(dynamic_fids):
        raise ValueError("Static and dynamic FID lists must have the same length")
    
    differences = [s - d for s, d in zip(static_fids, dynamic_fids)]
    mean_diff = sum(differences) / len(differences)
    std_diff = (sum((d - mean_diff) ** 2 for d in differences) / len(differences)) ** 0.5
    
    return {
        "mean_difference": mean_diff,
        "std_difference": std_diff,
        "n_samples": len(differences)
    }

def perform_bootstrap_test(differences: List[float], n_resamples: int = 1000) -> Dict[str, Any]:
    """Performs a bootstrap test on the differences."""
    import numpy as np
    bootstrap_means = []
    for _ in range(n_resamples):
        sample = np.random.choice(differences, size=len(differences), replace=True)
        bootstrap_means.append(np.mean(sample))
    
    mean = np.mean(bootstrap_means)
    std = np.std(bootstrap_means)
    
    # Compute p-value (two-tailed)
    observed_mean = np.mean(differences)
    p_value = 2 * min(
        np.mean(bootstrap_means <= observed_mean),
        np.mean(bootstrap_means >= observed_mean)
    )
    
    return {
        "mean": mean,
        "std": std,
        "p_value": p_value,
        "n_resamples": n_resamples
    }

def run_statistical_analysis():
    """Runs the full statistical analysis."""
    logger.info("Running statistical analysis...")
    
    # Run benchmark with multiple seeds
    seeds = [42, 456, 789, 1011, 2024]
    static_fids = []
    dynamic_fids = []
    
    for seed in seeds:
        results = run_benchmark_with_seed(seed)
        static_fids.append(results["static_fid"])
        dynamic_fids.append(results["dynamic_fid"])
    
    # Compute paired difference stats
    stats = compute_paired_difference_stats(static_fids, dynamic_fids)
    
    # Perform bootstrap test
    differences = [s - d for s, d in zip(static_fids, dynamic_fids)]
    bootstrap_results = perform_bootstrap_test(differences)
    
    # Prepare output
    output = {
        "mean": stats["mean_difference"],
        "std": stats["std_difference"],
        "bootstrap_results": bootstrap_results,
        "statistical_limitations": "Analysis based on N=5 seeds. Parametric tests may have low power."
    }
    
    output_path = Path("data/results/statistical_analysis.json")
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    logger.info(f"Statistical analysis results saved to {output_path}")

def main():
    """Entry point for the stats analysis script."""
    run_statistical_analysis()

if __name__ == "__main__":
    main()
