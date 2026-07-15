import warnings
import time
import tracemalloc
import os
import sys
import csv
import argparse
from typing import List, Dict, Union, Optional

import numpy as np
import pandas as pd

from code.config import load_config, set_seed, validate_config, parse_cli_args
from code.data_generator import generate_data
from code.estimators import (
    run_naive_ttest_with_warning,
    run_cluster_robust_ttest,
    run_block_permutation,
)
from code.analysis import aggregate_errors

# Constants for memory limits (in GB)
MEMORY_LIMIT_GB = 7.0
MEMORY_SOFT_LIMIT_GB = 6.0  # Threshold for down-sampling
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_GB * 1024**3
MEMORY_SOFT_LIMIT_BYTES = MEMORY_SOFT_LIMIT_GB * 1024**3

def estimate_memory_footprint(n_clusters: int, n_obs_per_cluster: int, df_rows: int = 0) -> float:
    """
    Estimate memory footprint of the simulation data frame.
    Assumes float64 for numeric columns and object/string overhead for categoricals.
    Approximate calculation:
    - Cluster ID: int64 (8 bytes)
    - Treatment: bool/int (1-4 bytes, rounded to 8 for alignment)
    - Outcome: float64 (8 bytes)
    - Overhead per row ~ 64 bytes (pandas metadata + alignment)
    """
    if df_rows > 0:
        # If we have an existing dataframe, use its info
        return df_rows * 88.0  # Rough estimate based on typical pandas overhead

    # Estimate for a full iteration
    total_obs = n_clusters * n_obs_per_cluster
    # 3 columns: cluster_id, treatment, outcome
    # 8 + 8 + 8 = 24 bytes data + ~64 bytes overhead per row
    return total_obs * 88.0

def downsample_clusters(data: pd.DataFrame, target_rows: int) -> pd.DataFrame:
    """
    Downsample the data by randomly selecting rows within each cluster
    to keep total rows close to target_rows, preserving cluster structure.
    """
    if len(data) <= target_rows:
        return data

    # Group by cluster and sample evenly
    n_clusters = data['cluster_id'].nunique()
    rows_per_cluster = max(1, target_rows // n_clusters)

    sampled_dfs = []
    for _, group in data.groupby('cluster_id'):
        if len(group) > rows_per_cluster:
            sampled = group.sample(n=rows_per_cluster, random_state=42)
        else:
            sampled = group
        sampled_dfs.append(sampled)

    return pd.concat(sampled_dfs, ignore_index=True)

def log_timing(iteration: int, elapsed_seconds: float, icc: float, method: str, output_path: str = "data/timing.csv"):
    """
    Append timing data to a CSV file.
    Creates the file with headers if it doesn't exist.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    file_exists = os.path.exists(output_path)

    with open(output_path, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['iteration', 'elapsed_seconds', 'icc', 'method'])
        writer.writerow([iteration, elapsed_seconds, icc, method])

def log_memory(peak_memory_bytes: float, iteration: int, icc: float, method: str, output_path: str = "data/memory.csv"):
    """
    Append peak memory usage to a CSV file.
    Creates the file with headers if it doesn't exist.
    Raises ValueError if peak memory exceeds MEMORY_LIMIT_GB.
    """
    peak_memory_gb = peak_memory_bytes / (1024**3)

    if peak_memory_gb > MEMORY_LIMIT_GB:
        raise MemoryError(
            f"Peak memory usage {peak_memory_gb:.2f} GB exceeds limit of {MEMORY_LIMIT_GB} GB. "
            "Simulation aborted to prevent system instability."
        )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    file_exists = os.path.exists(output_path)

    with open(output_path, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['iteration', 'peak_memory_gb', 'icc', 'method'])
        writer.writerow([iteration, peak_memory_gb, icc, method])

def run_baseline_simulation(icc: float, n_iterations: int, seed: int, n_clusters: int = None, n_obs: int = None) -> List[Dict]:
    """
    Run the baseline simulation loop with performance monitoring.
    """
    config = load_config()
    if n_clusters is None:
        n_clusters = config.get('n_clusters', 100)
    if n_obs is None:
        n_obs = config.get('n_obs_per_cluster', 10)

    results = []
    start_time = time.time()

    # Initialize memory tracking
    tracemalloc.start()

    for i in range(n_iterations):
        iteration_start = time.time()
        set_seed(seed + i)

        # Check memory footprint before generating data
        est_mem = estimate_memory_footprint(n_clusters, n_obs)
        if est_mem > MEMORY_SOFT_LIMIT_BYTES:
            # Downsample to stay within soft limit
            target_rows = int(MEMORY_SOFT_LIMIT_BYTES / 88.0)
            # Generate full data first, then downsample (simple approach)
            # Or adjust n_obs dynamically
            adjusted_n_obs = max(1, target_rows // n_clusters)
            if adjusted_n_obs < n_obs:
                warnings.warn(f"Downsampling from {n_obs} to {adjusted_n_obs} obs/cluster due to memory constraints.")
                n_obs = adjusted_n_obs

        data = generate_data(n_clusters, n_obs, icc, seed + i)

        # Run naive t-test
        p_val = run_naive_ttest_with_warning(data, 'treatment', 'outcome')

        iteration_end = time.time()
        elapsed = iteration_end - iteration_start

        # Log timing
        log_timing(i, elapsed, icc, 'naive')

        # Log memory
        current, peak = tracemalloc.get_traced_memory()
        log_memory(peak, i, icc, 'naive')

        results.append({
            'iteration': i,
            'icc': icc,
            'method': 'naive',
            'p_value': p_val,
            'elapsed_seconds': elapsed
        })

    tracemalloc.stop()
    total_time = time.time() - start_time
    print(f"Baseline simulation completed in {total_time:.2f} seconds.")

    return results

def run_robust_simulation(icc: float, n_iterations: int, seed: int, n_clusters: int = None, n_obs: int = None) -> List[Dict]:
    """
    Run the robust simulation loop with performance monitoring for all methods.
    """
    config = load_config()
    if n_clusters is None:
        n_clusters = config.get('n_clusters', 100)
    if n_obs is None:
        n_obs = config.get('n_obs_per_cluster', 10)

    results = []
    start_time = time.time()

    tracemalloc.start()

    for i in range(n_iterations):
        iteration_start = time.time()
        set_seed(seed + i)

        est_mem = estimate_memory_footprint(n_clusters, n_obs)
        if est_mem > MEMORY_SOFT_LIMIT_BYTES:
            target_rows = int(MEMORY_SOFT_LIMIT_BYTES / 88.0)
            adjusted_n_obs = max(1, target_rows // n_clusters)
            if adjusted_n_obs < n_obs:
                warnings.warn(f"Downsampling from {n_obs} to {adjusted_n_obs} obs/cluster due to memory constraints.")
                n_obs = adjusted_n_obs

        data = generate_data(n_clusters, n_obs, icc, seed + i)

        methods = [
            ('naive', run_naive_ttest_with_warning, {'treatment_col': 'treatment', 'outcome_col': 'outcome'}),
            ('cluster_robust', run_cluster_robust_ttest, {'treatment_col': 'treatment', 'outcome_col': 'outcome', 'cluster_id_col': 'cluster_id'}),
            ('block_permutation', run_block_permutation, {'treatment_col': 'treatment', 'outcome_col': 'outcome', 'cluster_id_col': 'cluster_id', 'n_permutations': 100})
        ]

        for method_name, func, kwargs in methods:
            method_start = time.time()
            p_val = func(data, **kwargs)
            method_end = time.time()
            elapsed = method_end - method_start

            log_timing(i, elapsed, icc, method_name)

            current, peak = tracemalloc.get_traced_memory()
            log_memory(peak, i, icc, method_name)

            results.append({
                'iteration': i,
                'icc': icc,
                'method': method_name,
                'p_value': p_val,
                'elapsed_seconds': elapsed
            })

    tracemalloc.stop()
    total_time = time.time() - start_time
    print(f"Robust simulation completed in {total_time:.2f} seconds.")

    return results

def run_full_simulation(icc_values: List[float], n_iterations: int, seed: int, n_clusters: int = None, n_obs: int = None) -> List[Dict]:
    """
    Run simulations for multiple ICC values.
    """
    all_results = []
    for icc in icc_values:
        print(f"Running simulation for ICC={icc}...")
        results = run_robust_simulation(icc, n_iterations, seed, n_clusters, n_obs)
        all_results.extend(results)
    return all_results

def parse_args():
    parser = argparse.ArgumentParser(description="Run A/B test simulation with performance monitoring.")
    parser.add_argument('--icc', type=float, default=None, help="Specific ICC value to test.")
    parser.add_argument('--icc-range', type=str, default=None, help="Comma-separated list of ICC values.")
    parser.add_argument('--icc-step', type=float, default=0.1, help="Step size for ICC range.")
    parser.add_argument('--iterations', type=int, default=100, help="Number of iterations per ICC.")
    parser.add_argument('--seed', type=int, default=42, help="Random seed.")
    parser.add_argument('--n-clusters', type=int, default=None, help="Number of clusters.")
    parser.add_argument('--n-obs', type=int, default=None, help="Observations per cluster.")
    return parser.parse_args()

def main():
    args = parse_args()
    config = parse_cli_args(args)
    validate_config(config)

    if args.icc is not None:
        icc_values = [args.icc]
    elif args.icc_range:
        icc_values = [float(x) for x in args.icc_range.split(',')]
    else:
        # Default range from config
        icc_values = config.get('icc_range', [0.0, 0.1, 0.2, 0.3, 0.4, 0.5])

    results = run_full_simulation(
        icc_values=icc_values,
        n_iterations=args.iterations,
        seed=args.seed,
        n_clusters=args.n_clusters,
        n_obs=args.n_obs
    )

    # Save results
    df = pd.DataFrame(results)
    output_path = "data/derived/simulation_results.csv"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Results saved to {output_path}")

if __name__ == "__main__":
    main()