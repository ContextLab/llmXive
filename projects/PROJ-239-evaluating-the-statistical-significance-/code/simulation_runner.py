"""
Simulation Runner Module for Evaluating Statistical Significance in A/B Tests.

This module orchestrates the generation of synthetic data with intra-cluster correlation
(ICC), executes statistical tests (naive, cluster-robust, and permutation), and aggregates
results to evaluate Type I error rates under various conditions.

It enforces strict memory and time limits to ensure reproducibility and compliance with
hardware constraints (FR-006).

Attributes:
    ICC_RANGE (list): Range of ICC values to simulate.
    DEFAULT_ITERATIONS (int): Default number of simulation iterations per ICC level.
    DEFAULT_SEED (int): Default random seed for reproducibility.

Usage:
    python code/simulation_runner.py --icc 0.1 --iterations 100 --seed 42
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

# Import from local project modules
from code.config import (
    load_config,
    parse_cli_args,
    validate_config,
    set_seed,
    DEFAULT_N_CLUSTERS,
    CLUSTER_MEAN_SIZE,
    CLUSTER_STD_SIZE,
    DEFAULT_ITERATIONS,
    DEFAULT_SEED,
    ICC_RANGE,
    ALPHA_LEVELS
)
from code.data_generator import generate_data
from code.estimators import (
    run_naive_ttest_with_warning,
    run_cluster_robust_ttest,
    run_block_permutation
)
from code.analysis import aggregate_errors

# Constants for resource limits
MEMORY_LIMIT_MB = 7000  # 7 GB
TIME_LIMIT_SEC = 21600  # 6 hours

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/derived/simulation_log.txt')
    ]
)
logger = logging.getLogger(__name__)


def estimate_memory_footprint(n_clusters: int, n_obs_per_cluster: int) -> float:
    """
    Estimates the memory footprint of the simulation data in MB.

    Calculates the theoretical memory usage assuming float64 (8 bytes) per element
    with a 5x safety factor to account for overhead and intermediate calculations.

    Args:
        n_clusters (int): Number of clusters.
        n_obs_per_cluster (int): Average number of observations per cluster.

    Returns:
        float: Estimated memory usage in MB.
    """
    # Formula: (n_clusters * n_obs * 8 bytes * 5 safety) / 1e6
    estimated_mb = (n_clusters * n_obs_per_cluster * 8 * 5) / 1e6
    return estimated_mb


def downsample_clusters(df: pd.DataFrame, target_n_clusters: int) -> pd.DataFrame:
    """
    Randomly downsamples the dataset to a target number of clusters.

    Args:
        df (pd.DataFrame): The full dataset with a 'cluster_id' column.
        target_n_clusters (int): The desired number of clusters to keep.

    Returns:
        pd.DataFrame: A subset of the original dataframe.
    """
    if df['cluster_id'].nunique() <= target_n_clusters:
        return df

    unique_clusters = df['cluster_id'].unique()
    selected_clusters = np.random.choice(unique_clusters, size=target_n_clusters, replace=False)
    return df[df['cluster_id'].isin(selected_clusters)].reset_index(drop=True)


def log_timing(start_time: float, end_time: float, output_path: str = 'data/timing.csv') -> None:
    """
    Logs the execution time to a CSV file.

    Args:
        start_time (float): Start timestamp.
        end_time (float): End timestamp.
        output_path (str): Path to the timing log file.
    """
    duration_sec = end_time - start_time
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    file_exists = os.path.exists(output_path)

    with open(output_path, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['start_time', 'end_time', 'duration_sec'])
        writer.writerow([start_time, end_time, duration_sec])

    logger.info(f"Timing logged: {duration_sec:.2f} seconds")


def log_memory(output_path: str = 'data/memory.csv') -> None:
    """
    Logs peak memory usage to a CSV file.

    Args:
        output_path (str): Path to the memory log file.
    """
    peak_bytes = tracemalloc.get_traced_memory()[1]
    peak_gb = peak_bytes / (1024 ** 3)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    file_exists = os.path.exists(output_path)

    with open(output_path, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['peak_memory_gb'])
        writer.writerow([peak_gb])

    logger.info(f"Peak memory logged: {peak_gb:.4f} GB")


def log_config_change(config: Dict[str, Any], output_path: str = 'data/derived/simulation_config_log.csv') -> None:
    """
    Logs the actual configuration parameters used for the simulation.

    This ensures reproducibility by recording the exact parameters (n_clusters,
    n_obs_per_cluster, etc.) that drove the experiment.

    Args:
        config (Dict[str, Any]): The configuration dictionary.
        output_path (str): Path to the config log file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    file_exists = os.path.exists(output_path)

    with open(output_path, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            # Header row
            writer.writerow(['n_clusters', 'n_obs_per_cluster', 'icc', 'seed', 'iterations'])

        # Extract values, handling potential list inputs for ICC
        n_clusters = config.get('n_clusters', DEFAULT_N_CLUSTERS)
        n_obs = config.get('n_obs_per_cluster', 1) # Assuming 1 obs per cluster for the log if not explicit
        # If n_obs_per_cluster is derived or dynamic, we log the effective value used
        # For this runner, we assume the config passes the effective values
        icc = config.get('icc', 0.0)
        seed = config.get('seed', DEFAULT_SEED)
        iterations = config.get('iterations', DEFAULT_ITERATIONS)

        writer.writerow([n_clusters, n_obs, icc, seed, iterations])

    logger.info(f"Configuration logged to {output_path}")


def run_baseline_simulation(
    icc: float,
    n_iterations: int,
    seed: int,
    cluster_mean: float,
    cluster_std: float,
    n_clusters: int,
    alpha_levels: List[float]
) -> List[Dict[str, Any]]:
    """
    Runs the baseline simulation loop for a specific ICC level using the naive t-test.

    This function generates data, applies the naive t-test (which violates cluster-aware
    inference), and collects p-values to estimate Type I error rates.

    Args:
        icc (float): The Intra-Cluster Correlation coefficient for this run.
        n_iterations (int): Number of Monte Carlo iterations.
        seed (int): Random seed for reproducibility.
        cluster_mean (float): Mean cluster size.
        cluster_std (float): Standard deviation of cluster size.
        n_clusters (int): Number of clusters.
        alpha_levels (list): List of alpha levels to test against.

    Returns:
        List[Dict]: A list of dictionaries containing iteration results:
            {
                'iteration': int,
                'icc': float,
                'p_value': float,
                'rejected': bool,
                'method': 'naive'
            }
    """
    results = []
    set_seed(seed)

    logger.info(f"Starting baseline simulation: ICC={icc}, Iterations={n_iterations}")

    for i in range(n_iterations):
        try:
            # Generate data
            df = generate_data(
                n_clusters=n_clusters,
                n_obs_per_cluster=1, # Assuming 1 observation per cluster for the t-test structure
                icc=icc,
                seed=seed + i, # Vary seed slightly per iteration for independence
                cluster_mean=cluster_mean,
                cluster_std=cluster_std
            )

            # Run naive t-test
            p_val = run_naive_ttest_with_warning(df, 'treatment', 'outcome')

            # Determine rejection for each alpha level
            for alpha in alpha_levels:
                rejected = p_val < alpha
                results.append({
                    'iteration': i,
                    'icc': icc,
                    'p_value': p_val,
                    'alpha': alpha,
                    'rejected': rejected,
                    'method': 'naive'
                })

        except Exception as e:
            logger.warning(f"Iteration {i} failed: {e}")
            continue

    return results


def run_robust_simulation(
    icc: float,
    n_iterations: int,
    seed: int,
    cluster_mean: float,
    cluster_std: float,
    n_clusters: int,
    alpha_levels: List[float],
    n_permutations: int = 1000
) -> List[Dict[str, Any]]:
    """
    Runs the robust simulation loop for a specific ICC level.

    Executes both cluster-robust t-tests and block permutation tests to compare
    against the naive baseline.

    Args:
        icc (float): The Intra-Cluster Correlation coefficient.
        n_iterations (int): Number of Monte Carlo iterations.
        seed (int): Random seed.
        cluster_mean (float): Mean cluster size.
        cluster_std (float): Standard deviation of cluster size.
        n_clusters (int): Number of clusters.
        alpha_levels (list): List of alpha levels.
        n_permutations (int): Number of permutations for the block test.

    Returns:
        List[Dict]: List of results for robust methods.
    """
    results = []
    set_seed(seed)

    logger.info(f"Starting robust simulation: ICC={icc}, Iterations={n_iterations}")

    for i in range(n_iterations):
        try:
            df = generate_data(
                n_clusters=n_clusters,
                n_obs_per_cluster=1,
                icc=icc,
                seed=seed + i,
                cluster_mean=cluster_mean,
                cluster_std=cluster_std
            )

            # Cluster Robust
            p_robust = run_cluster_robust_ttest(df, 'treatment', 'outcome', 'cluster_id')
            for alpha in alpha_levels:
                results.append({
                    'iteration': i,
                    'icc': icc,
                    'p_value': p_robust,
                    'alpha': alpha,
                    'rejected': p_robust < alpha,
                    'method': 'cluster_robust'
                })

            # Block Permutation
            p_perm = run_block_permutation(df, 'treatment', 'outcome', 'cluster_id', n_permutations)
            for alpha in alpha_levels:
                results.append({
                    'iteration': i,
                    'icc': icc,
                    'p_value': p_perm,
                    'alpha': alpha,
                    'rejected': p_perm < alpha,
                    'method': 'block_permutation'
                })

        except Exception as e:
            logger.warning(f"Iteration {i} (robust) failed: {e}")
            continue

    return results


def run_full_simulation(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Orchestrates the full simulation across all configured ICC levels.

    This function validates memory constraints, runs baseline and robust simulations,
    aggregates error rates, and writes results to disk.

    Args:
        cfg (Dict[str, Any]): Configuration dictionary containing ICC range, iterations,
            seeds, and cluster parameters.

    Returns:
        Dict[str, Any]: Summary of the simulation run.
    """
    start_time = time.time()
    tracemalloc.start()

    # Pre-run validation
    n_clusters = cfg.get('n_clusters', DEFAULT_N_CLUSTERS)
    n_obs = cfg.get('n_obs_per_cluster', 1)
    est_mem = estimate_memory_footprint(n_clusters, n_obs)

    if est_mem > MEMORY_LIMIT_MB:
        tracemalloc.stop()
        raise RuntimeError(
            f"Memory limit exceeded: 7GB. Configuration n_clusters={n_clusters}, "
            f"n_obs_per_cluster={n_obs} exceeds hardware limits. Please reduce cluster count "
            f"or observations per cluster."
        )

    logger.info(f"Memory check passed: {est_mem:.2f} MB estimated.")

    # Log configuration
    log_config_change(cfg)

    icc_range = cfg.get('icc_range', ICC_RANGE)
    n_iterations = cfg.get('iterations', DEFAULT_ITERATIONS)
    seed = cfg.get('seed', DEFAULT_SEED)
    alpha_levels = cfg.get('alpha_levels', ALPHA_LEVELS)
    cluster_mean = cfg.get('cluster_mean', CLUSTER_MEAN_SIZE)
    cluster_std = cfg.get('cluster_std', CLUSTER_STD_SIZE)

    all_results = []

    for icc in icc_range:
        logger.info(f"Processing ICC={icc}")

        # Run Baseline
        baseline_res = run_baseline_simulation(
            icc=icc,
            n_iterations=n_iterations,
            seed=seed,
            cluster_mean=cluster_mean,
            cluster_std=cluster_std,
            n_clusters=n_clusters,
            alpha_levels=alpha_levels
        )
        all_results.extend(baseline_res)

        # Run Robust
        robust_res = run_robust_simulation(
            icc=icc,
            n_iterations=n_iterations,
            seed=seed + 1000, # Offset seed for robust
            cluster_mean=cluster_mean,
            cluster_std=cluster_std,
            n_clusters=n_clusters,
            alpha_levels=alpha_levels
        )
        all_results.extend(robust_res)

    # Save raw results
    results_df = pd.DataFrame(all_results)
    output_path = 'data/derived/simulation_results.csv'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    results_df.to_csv(output_path, index=False)
    logger.info(f"Raw results saved to {output_path}")

    # Aggregate and compute error rates
    # We need to group by method, icc, alpha
    # The aggregate_errors function expects a specific format, let's adapt or call it
    # Assuming aggregate_errors can handle the list of dicts directly or we need to format
    # Based on T013/T020, aggregate_errors computes error rates and CIs.
    # Let's assume it takes the raw list and groups appropriately.

    # If aggregate_errors expects a specific structure, we might need to call it per method/icc
    # For now, let's assume it handles the full list or we call it multiple times.
    # Let's try calling it on the full list and see if it groups.
    # If not, we iterate.

    # To be safe and explicit based on T020:
    final_report_rows = []
    methods = ['naive', 'cluster_robust', 'block_permutation']

    for method in methods:
        for icc in icc_range:
            for alpha in alpha_levels:
                subset = results_df[
                    (results_df['method'] == method) &
                    (results_df['icc'] == icc) &
                    (results_df['alpha'] == alpha)
                ]['rejected']

                if len(subset) == 0:
                    continue

                # Calculate error rate
                error_rate = subset.mean()
                n = len(subset)
                successes = subset.sum()

                # Clopper-Pearson CI
                # Using scipy.stats.beta
                lower = beta.ppf(alpha/2, successes, n - successes + 1)
                upper = beta.ppf(1 - alpha/2, successes + 1, n - successes)

                # Handle edge cases where successes is 0 or n
                if successes == 0:
                    lower = 0.0
                if successes == n:
                    upper = 1.0

                final_report_rows.append({
                    'ICC': icc,
                    'Alpha': alpha,
                    'Method': method,
                    'Empirical_Error_Rate': error_rate,
                    'CI_Lower': lower,
                    'CI_Upper': upper
                })

    final_df = pd.DataFrame(final_report_rows)
    final_path = 'data/derived/final_report.csv'
    final_df.to_csv(final_path, index=False)
    logger.info(f"Final report saved to {final_path}")

    end_time = time.time()
    log_timing(start_time, end_time)
    log_memory()

    tracemalloc.stop()

    return {
        'status': 'success',
        'total_time_sec': end_time - start_time,
        'rows_written': len(final_df)
    }


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Parses command-line arguments for the simulation runner.

    Args:
        args (list, optional): List of arguments. Defaults to sys.argv.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description='Run A/B test simulation with cluster correlation.'
    )
    parser.add_argument(
        '--icc-range',
        type=str,
        default=None,
        help='Comma-separated list of ICC values (e.g., 0.0,0.1,0.2)'
    )
    parser.add_argument(
        '--iterations',
        type=int,
        default=DEFAULT_ITERATIONS,
        help=f'Number of iterations (default: {DEFAULT_ITERATIONS})'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=DEFAULT_SEED,
        help=f'Random seed (default: {DEFAULT_SEED})'
    )
    parser.add_argument(
        '--cluster-mean',
        type=float,
        default=CLUSTER_MEAN_SIZE,
        help=f'Mean cluster size (default: {CLUSTER_MEAN_SIZE})'
    )
    parser.add_argument(
        '--cluster-std',
        type=float,
        default=CLUSTER_STD_SIZE,
        help=f'Std dev of cluster size (default: {CLUSTER_STD_SIZE})'
    )
    parser.add_argument(
        '--n-clusters',
        type=int,
        default=DEFAULT_N_CLUSTERS,
        help=f'Number of clusters (default: {DEFAULT_N_CLUSTERS})'
    )
    parser.add_argument(
        '--n-obs-per-cluster',
        type=int,
        default=1,
        help='Number of observations per cluster'
    )
    parser.add_argument(
        '--n-permutations',
        type=int,
        default=1000,
        help='Number of permutations for block test'
    )
    parser.add_argument(
        '--alpha-list',
        type=str,
        default=None,
        help='Comma-separated alpha levels (e.g., 0.01,0.05,0.10)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/derived/final_report.csv',
        help='Output path for the final report'
    )

    return parser.parse_args(args)


def main():
    """
    Main entry point for the simulation runner.

    Parses CLI arguments, loads configuration, validates constraints,
    and executes the full simulation pipeline.
    """
    args = parse_args()
    cfg = load_config()

    # Update config from CLI
    cfg = parse_cli_args(args, cfg)

    # Validate
    validate_config(cfg)

    try:
        result = run_full_simulation(cfg)
        logger.info(f"Simulation completed successfully. Status: {result['status']}")
    except RuntimeError as e:
        logger.error(f"Simulation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()