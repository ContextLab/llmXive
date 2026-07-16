"""Simulation runner for baseline and robust A/B test simulations.

This module implements the core simulation loop that generates clustered data,
runs statistical tests (naive and robust), and collects p-values for analysis.
It includes memory and time monitoring to enforce resource constraints.

Principles:
- VI (Cluster-Aware Inference): Baseline method intentionally violates this for comparison.
- VII (Simulation Transparency): All parameters are logged and reproducible.
"""
import warnings
import time
import tracemalloc
import os
import sys
import csv
import argparse
import logging
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd

# Import from project modules
from code.config import set_seed, load_config, validate_config, parse_cli_args
from code.data_generator import generate_data
from code.estimators import (
    run_naive_ttest_with_warning,
    run_cluster_robust_ttest,
    run_block_permutation
)
from code.analysis import aggregate_errors, select_ci_method

# Constants
MEMORY_LIMIT_GB = 6.5
TIME_LIMIT_SEC = 21600  # 6 hours
MAX_DOWNSAMPLE_RETRIES = 3

def estimate_memory_footprint(n_clusters: int, n_obs_per_cluster: int) -> float:
    """Estimate memory footprint in GB for a single iteration.
    
    Args:
        n_clusters: Number of clusters.
        n_obs_per_cluster: Observations per cluster.
        
    Returns:
        Estimated memory usage in GB.
    """
    # Rough estimate: DataFrame with ~5 columns, float64
    # Each row: ~40 bytes (5 cols * 8 bytes)
    total_rows = n_clusters * n_obs_per_cluster
    estimated_bytes = total_rows * 40 * 2  # Factor of 2 for overhead
    return estimated_bytes / (1024 ** 3)

def downsample_clusters(n_obs_per_cluster: int) -> int:
    """Reduce observations per cluster by half.
    
    Args:
        n_obs_per_cluster: Current observations per cluster.
        
    Returns:
        New reduced count.
    """
    return max(1, n_obs_per_cluster // 2)

def log_timing(iteration: int, elapsed: float, log_file: str = 'data/timing.csv') -> None:
    """Log timing information to CSV.
    
    Args:
        iteration: Current iteration number.
        elapsed: Elapsed time in seconds.
        log_file: Path to timing log file.
    """
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    file_exists = os.path.exists(log_file)
    with open(log_file, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['iteration', 'elapsed_sec'])
        writer.writerow([iteration, elapsed])

def log_memory(iteration: int, peak_gb: float, log_file: str = 'data/memory.csv') -> None:
    """Log memory usage to CSV.
    
    Args:
        iteration: Current iteration number.
        peak_gb: Peak memory usage in GB.
        log_file: Path to memory log file.
    """
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    file_exists = os.path.exists(log_file)
    with open(log_file, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['iteration', 'peak_memory_gb'])
        writer.writerow([iteration, peak_gb])

def run_baseline_simulation(
    icc: float,
    n_iterations: int,
    seed: int,
    n_clusters: int = 100,
    n_obs_per_cluster: int = 100,
    alpha: float = 0.05
) -> List[Dict[str, Any]]:
    """Run baseline simulation for a single ICC value.
    
    This function generates clustered data under the null hypothesis (H0: no treatment effect),
    runs a naive independent t-test (which violates cluster-aware inference), and collects p-values.
    
    Args:
        icc: Intra-cluster correlation coefficient.
        n_iterations: Number of simulation iterations.
        seed: Random seed for reproducibility.
        n_clusters: Number of clusters.
        n_obs_per_cluster: Observations per cluster.
        alpha: Significance level.
        
    Returns:
        List of result dictionaries with keys: iteration, icc, p_value, rejected.
        
    Raises:
        RuntimeError: If memory constraints cannot be satisfied after retries.
    """
    set_seed(seed)
    results = []
    current_n_obs = n_obs_per_cluster
    retries = 0
    
    logging.info(f"Starting baseline simulation: ICC={icc}, iterations={n_iterations}, "
                 f"clusters={n_clusters}, obs/cluster={current_n_obs}")

    # Pre-check memory
    mem_estimate = estimate_memory_footprint(n_clusters, current_n_obs)
    if mem_estimate > 6.0:  # Pre-check threshold
        logging.warning(f"Memory estimate ({mem_estimate:.2f} GB) exceeds 6GB threshold. "
                        f"Attempting downsampling...")
        while retries < MAX_DOWNSAMPLE_RETRIES and mem_estimate > 6.0:
            current_n_obs = downsample_clusters(current_n_obs)
            mem_estimate = estimate_memory_footprint(n_clusters, current_n_obs)
            retries += 1
            logging.info(f"Retry {retries}: Reduced n_obs_per_cluster to {current_n_obs}, "
                         f"new estimate: {mem_estimate:.2f} GB")
        
        if mem_estimate > 6.0:
            raise RuntimeError(
                f"Memory limit exceeded after {MAX_DOWNSAMPLE_RETRIES} downsampling retries. "
                f"Final estimate: {mem_estimate:.2f} GB, n_clusters={n_clusters}, "
                f"n_obs_per_cluster={current_n_obs}"
            )

    tracemalloc.start()
    start_time = time.time()

    for iteration in range(n_iterations):
        # Check time limit
        elapsed = time.time() - start_time
        if elapsed > TIME_LIMIT_SEC:
            tracemalloc.stop()
            raise RuntimeError(f"Time limit exceeded: {elapsed:.2f} seconds > {TIME_LIMIT_SEC} seconds")

        try:
            # Generate data
            data = generate_data(
                n_clusters=n_clusters,
                n_obs_per_cluster=current_n_obs,
                icc=icc,
                seed=seed + iteration
            )

            # Run naive t-test (with warning)
            p_value = run_naive_ttest_with_warning(data, 'treatment', 'outcome')

            # Record result
            results.append({
                'iteration': iteration,
                'icc': icc,
                'p_value': p_value,
                'rejected': p_value < alpha
            })

            # Post-check memory
            current_mem, peak_mem = tracemalloc.get_traced_memory()
            peak_gb = peak_mem / (1024 ** 3)
            if peak_gb > MEMORY_LIMIT_GB:
                tracemalloc.stop()
                raise RuntimeError(
                    f"Memory limit exceeded: {peak_gb:.2f} GB > {MEMORY_LIMIT_GB} GB. "
                    f"Down-sampling failed to prevent OOM."
                )

            # Log timing and memory periodically
            if (iteration + 1) % 100 == 0:
                log_timing(iteration, elapsed)
                log_memory(iteration, peak_gb)
                logging.info(f"Iteration {iteration + 1}/{n_iterations} completed. "
                             f"P-value: {p_value:.4f}, Peak Memory: {peak_gb:.2f} GB")

        except Exception as e:
            logging.warning(f"Iteration {iteration} failed: {str(e)}. Skipping.")
            continue

    tracemalloc.stop()
    total_time = time.time() - start_time
    logging.info(f"Baseline simulation completed. Total time: {total_time:.2f} seconds. "
                 f"Results collected: {len(results)}")

    return results

def run_robust_simulation(
    icc: float,
    n_iterations: int,
    seed: int,
    n_clusters: int = 100,
    n_obs_per_cluster: int = 100,
    alpha: float = 0.05,
    n_permutations: int = 1000
) -> List[Dict[str, Any]]:
    """Run robust simulation for a single ICC value.
    
    This function generates clustered data and runs both cluster-robust t-test
    and block permutation test, collecting p-values for comparison.
    
    Args:
        icc: Intra-cluster correlation coefficient.
        n_iterations: Number of simulation iterations.
        seed: Random seed for reproducibility.
        n_clusters: Number of clusters.
        n_obs_per_cluster: Observations per cluster.
        alpha: Significance level.
        n_permutations: Number of permutations for block test.
        
    Returns:
        List of result dictionaries with keys: iteration, icc, method, p_value, rejected.
    """
    set_seed(seed)
    results = []
    methods = ['cluster_robust', 'block_permutation']
    
    logging.info(f"Starting robust simulation: ICC={icc}, iterations={n_iterations}, "
                 f"methods={methods}")

    for iteration in range(n_iterations):
        try:
            # Generate data
            data = generate_data(
                n_clusters=n_clusters,
                n_obs_per_cluster=n_obs_per_cluster,
                icc=icc,
                seed=seed + iteration
            )

            # Run cluster-robust t-test
            p_robust = run_cluster_robust_ttest(data, 'treatment', 'outcome', 'cluster_id')
            results.append({
                'iteration': iteration,
                'icc': icc,
                'method': 'cluster_robust',
                'p_value': p_robust,
                'rejected': p_robust < alpha
            })

            # Run block permutation test
            p_perm = run_block_permutation(data, 'treatment', 'outcome', 'cluster_id', n_permutations)
            results.append({
                'iteration': iteration,
                'icc': icc,
                'method': 'block_permutation',
                'p_value': p_perm,
                'rejected': p_perm < alpha
            })

        except Exception as e:
            logging.warning(f"Iteration {iteration} failed: {str(e)}. Skipping.")
            continue

    logging.info(f"Robust simulation completed. Results collected: {len(results)}")
    return results

def run_full_simulation(
    cfg: Dict[str, Any],
    output_baseline: Optional[str] = None,
    output_robust: Optional[str] = None
) -> Tuple[List[Dict], List[Dict]]:
    """Run full simulation across all ICC values.
    
    Args:
        cfg: Configuration dictionary.
        output_baseline: Path for baseline results CSV.
        output_robust: Path for robust results CSV.
        
    Returns:
        Tuple of (baseline_results, robust_results).
    """
    icc_range = cfg.get('icc_range', [0.0, 0.1, 0.2, 0.3, 0.4, 0.5])
    n_iterations = cfg.get('iterations', 1000)
    seed = cfg.get('seed', 42)
    n_clusters = cfg.get('n_clusters', 100)
    n_obs_per_cluster = cfg.get('n_obs_per_cluster', 100)
    alpha_levels = cfg.get('alpha_levels', [0.05])
    n_permutations = cfg.get('n_permutations', 1000)
    
    # Use first alpha level for simulation (aggregation handles multiple)
    alpha = alpha_levels[0]
    
    baseline_results = []
    robust_results = []
    
    logging.info(f"Starting full simulation for ICC range: {icc_range}")
    
    for icc in icc_range:
        logging.info(f"Running simulation for ICC={icc}")
        
        # Run baseline
        baseline = run_baseline_simulation(
            icc=icc,
            n_iterations=n_iterations,
            seed=seed,
            n_clusters=n_clusters,
            n_obs_per_cluster=n_obs_per_cluster,
            alpha=alpha
        )
        baseline_results.extend(baseline)
        
        # Run robust
        robust = run_robust_simulation(
            icc=icc,
            n_iterations=n_iterations,
            seed=seed,
            n_clusters=n_clusters,
            n_obs_per_cluster=n_obs_per_cluster,
            alpha=alpha,
            n_permutations=n_permutations
        )
        robust_results.extend(robust)
    
    # Save results
    if output_baseline:
        df_baseline = pd.DataFrame(baseline_results)
        df_baseline.to_csv(output_baseline, index=False)
        logging.info(f"Baseline results saved to {output_baseline}")
    
    if output_robust:
        df_robust = pd.DataFrame(robust_results)
        df_robust.to_csv(output_robust, index=False)
        logging.info(f"Robust results saved to {output_robust}")
    
    return baseline_results, robust_results

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.
    
    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(description='Simulation Runner for A/B Test Significance')
    parser.add_argument('--icc', type=float, help='Single ICC value to simulate')
    parser.add_argument('--iterations', type=int, default=1000, help='Number of simulation iterations')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--n-clusters', type=int, default=100, help='Number of clusters')
    parser.add_argument('--n-obs-per-cluster', type=int, default=100, help='Observations per cluster')
    parser.add_argument('--icc-range', type=str, help='Comma-separated ICC values')
    parser.add_argument('--icc-step', type=float, help='Step size for ICC range')
    parser.add_argument('--alpha', type=float, default=0.05, help='Significance level')
    parser.add_argument('--alpha-list', type=str, help='Comma-separated alpha levels')
    parser.add_argument('--n-permutations', type=int, default=1000, help='Number of permutations')
    parser.add_argument('--output-baseline', type=str, default='data/derived/baseline_results.csv',
                        help='Output path for baseline results')
    parser.add_argument('--output-robust', type=str, default='data/derived/robustResults.csv',
                        help='Output path for robust results')
    parser.add_argument('--mode', type=str, choices=['baseline', 'robust', 'full'], default='full',
                        help='Simulation mode')
    return parser.parse_args()

def main():
    """Main entry point for simulation runner."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    args = parse_args()
    cfg = load_config()
    cfg = parse_cli_args(args, cfg)
    
    # Validate configuration
    validate_config(cfg)
    
    # Run simulation based on mode
    if args.mode == 'baseline':
        baseline_results = run_baseline_simulation(
            icc=cfg['icc_range'][0] if len(cfg['icc_range']) == 1 else 0.1,
            n_iterations=cfg.get('iterations', 1000),
            seed=cfg.get('seed', 42),
            n_clusters=cfg.get('n_clusters', 100),
            n_obs_per_cluster=cfg.get('n_obs_per_cluster', 100),
            alpha=cfg['alpha_levels'][0]
        )
        df = pd.DataFrame(baseline_results)
        df.to_csv(cfg['output_baseline'], index=False)
        logging.info(f"Baseline results saved to {cfg['output_baseline']}")
        
    elif args.mode == 'robust':
        robust_results = run_robust_simulation(
            icc=cfg['icc_range'][0] if len(cfg['icc_range']) == 1 else 0.1,
            n_iterations=cfg.get('iterations', 1000),
            seed=cfg.get('seed', 42),
            n_clusters=cfg.get('n_clusters', 100),
            n_obs_per_cluster=cfg.get('n_obs_per_cluster', 100),
            alpha=cfg['alpha_levels'][0],
            n_permutations=cfg.get('n_permutations', 1000)
        )
        df = pd.DataFrame(robust_results)
        df.to_csv(cfg['output_robust'], index=False)
        logging.info(f"Robust results saved to {cfg['output_robust']}")
        
    else:  # full
        run_full_simulation(cfg, cfg['output_baseline'], cfg['output_robust'])
    
    logging.info("Simulation completed successfully.")

if __name__ == '__main__':
    main()
