import warnings
import time
import tracemalloc
import os
import sys
import csv
import logging
import argparse
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd

# Import project modules
from config import load_config, set_seed, validate_config, parse_cli_args
from data_generator import generate_data
from estimators import (
    run_naive_ttest_with_warning,
    run_cluster_robust_ttest,
    run_block_permutation
)
from analysis import aggregate_errors, select_ci_method

# Constants
MEMORY_LIMIT_GB = 7.0
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_GB * 1024**3
DOWNSAMPLE_THRESHOLD_GB = 6.0
DOWNSAMPLE_FACTOR = 0.8
MAX_RETRIES = 3

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/simulation.log')
    ]
)
logger = logging.getLogger(__name__)

def estimate_memory_footprint(n_clusters: int, n_obs_per_cluster: int, df_type: str = 'float64') -> int:
    """
    Estimate memory footprint of the dataframe in bytes.
    
    Args:
        n_clusters: Number of clusters
        n_obs_per_cluster: Observations per cluster
        df_type: Data type (assumed float64 for outcome)
    
    Returns:
        Estimated memory in bytes
    """
    total_rows = n_clusters * n_obs_per_cluster
    # Approximate: 4 columns (cluster_id, treatment, outcome, index) * 8 bytes * rows
    # Plus overhead for index and object columns
    base_size = total_rows * 4 * 8
    overhead = total_rows * 0.5  # 50% overhead for index, metadata
    return int(base_size + overhead)

def downsample_clusters(n_obs_per_cluster: int, factor: float = DOWNSAMPLE_FACTOR) -> int:
    """
    Reduce observations per cluster by a factor.
    
    Args:
        n_obs_per_cluster: Current observations per cluster
        factor: Downsampling factor (0.0 < factor < 1.0)
    
    Returns:
        New number of observations per cluster (minimum 1)
    """
    new_n = max(1, int(n_obs_per_cluster * factor))
    if new_n == n_obs_per_cluster:
        new_n = max(1, n_obs_per_cluster - 1)
    return new_n

def log_timing(iteration: int, duration: float, method: str, icc: float, seed: int):
    """Log timing information to data/timing.csv"""
    os.makedirs('data', exist_ok=True)
    file_path = 'data/timing.csv'
    file_exists = os.path.exists(file_path)
    
    with open(file_path, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['iteration', 'duration', 'method', 'icc', 'seed'])
        writer.writerow([iteration, duration, method, icc, seed])

def log_memory(iteration: int, current_mb: float, peak_mb: float, method: str, icc: float, seed: int):
    """Log memory usage to data/memory.csv"""
    os.makedirs('data', exist_ok=True)
    file_path = 'data/memory.csv'
    file_exists = os.path.exists(file_path)
    
    with open(file_path, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['iteration', 'current_mb', 'peak_mb', 'method', 'icc', 'seed'])
        writer.writerow([iteration, current_mb, peak_mb, method, icc, seed])

def run_baseline_simulation(icc: float, n_iterations: int, seed: int, n_clusters: int = 100, n_obs_per_cluster: int = 50) -> List[Dict]:
    """
    Run baseline simulation with naive t-test.
    
    Args:
        icc: Intraclass correlation coefficient
        n_iterations: Number of simulation iterations
        seed: Random seed
        n_clusters: Number of clusters
        n_obs_per_cluster: Observations per cluster
    
    Returns:
        List of result dictionaries
    """
    set_seed(seed)
    results = []
    
    for i in range(n_iterations):
        start_mem = tracemalloc.get_traced_memory() if tracemalloc.is_tracing() else (0, 0)
        
        # Memory check before generation
        estimated_mem = estimate_memory_footprint(n_clusters, n_obs_per_cluster)
        if estimated_mem > DOWNSAMPLE_THRESHOLD_GB * 1024**3:
            logger.warning(f"Iteration {i}: Estimated memory {estimated_mem / 1024**3:.2f}GB exceeds threshold. Downsampling.")
            n_obs_per_cluster = downsample_clusters(n_obs_per_cluster)
            estimated_mem = estimate_memory_footprint(n_clusters, n_obs_per_cluster)
            if estimated_mem > DOWNSAMPLE_THRESHOLD_GB * 1024**3:
                logger.error(f"Iteration {i}: Downsampling failed to reduce memory below threshold.")
                continue
        
        try:
            # Generate data
            data = generate_data(
                n_clusters=n_clusters,
                n_obs_per_cluster=n_obs_per_cluster,
                icc=icc,
                seed=seed + i
            )
            
            # Run naive t-test
            p_value = run_naive_ttest_with_warning(data, 'treatment', 'outcome')
            
            results.append({
                'iteration': i,
                'icc': icc,
                'p_value': p_value,
                'method': 'naive',
                'n_clusters': n_clusters,
                'n_obs_per_cluster': n_obs_per_cluster
            })
            
        except Exception as e:
            logger.warning(f"Iteration {i} failed: {str(e)}. Skipping.")
            continue
    
    return results

def run_robust_simulation(icc: float, n_iterations: int, seed: int, n_clusters: int = 100, n_obs_per_cluster: int = 50, n_permutations: int = 1000) -> List[Dict]:
    """
    Run simulation with robust methods.
    
    Args:
        icc: Intraclass correlation coefficient
        n_iterations: Number of simulation iterations
        seed: Random seed
        n_clusters: Number of clusters
        n_obs_per_cluster: Observations per cluster
        n_permutations: Number of permutations for block permutation test
    
    Returns:
        List of result dictionaries
    """
    set_seed(seed)
    results = []
    
    for i in range(n_iterations):
        # Memory check before generation
        estimated_mem = estimate_memory_footprint(n_clusters, n_obs_per_cluster)
        if estimated_mem > DOWNSAMPLE_THRESHOLD_GB * 1024**3:
            logger.warning(f"Iteration {i}: Estimated memory {estimated_mem / 1024**3:.2f}GB exceeds threshold. Downsampling.")
            n_obs_per_cluster = downsample_clusters(n_obs_per_cluster)
            estimated_mem = estimate_memory_footprint(n_clusters, n_obs_per_cluster)
            if estimated_mem > DOWNSAMPLE_THRESHOLD_GB * 1024**3:
                logger.error(f"Iteration {i}: Downsampling failed to reduce memory below threshold.")
                continue
        
        try:
            # Generate data
            data = generate_data(
                n_clusters=n_clusters,
                n_obs_per_cluster=n_obs_per_cluster,
                icc=icc,
                seed=seed + i
            )
            
            # Run cluster-robust t-test
            try:
                p_robust = run_cluster_robust_ttest(data, 'treatment', 'outcome', 'cluster_id')
                results.append({
                    'iteration': i,
                    'icc': icc,
                    'p_value': p_robust,
                    'method': 'cluster_robust',
                    'n_clusters': n_clusters,
                    'n_obs_per_cluster': n_obs_per_cluster
                })
            except Exception as e:
                logger.warning(f"Cluster-robust test failed at iteration {i}: {str(e)}")
            
            # Run block permutation test
            try:
                p_perm = run_block_permutation(data, 'treatment', 'outcome', 'cluster_id', n_permutations)
                results.append({
                    'iteration': i,
                    'icc': icc,
                    'p_value': p_perm,
                    'method': 'block_permutation',
                    'n_clusters': n_clusters,
                    'n_obs_per_cluster': n_obs_per_cluster
                })
            except Exception as e:
                logger.warning(f"Block permutation test failed at iteration {i}: {str(e)}")
            
        except Exception as e:
            logger.warning(f"Iteration {i} failed: {str(e)}. Skipping.")
            continue
    
    return results

def run_full_simulation(icc: float, n_iterations: int, seed: int, n_clusters: int = 100, n_obs_per_cluster: int = 50, n_permutations: int = 1000) -> Tuple[List[Dict], List[Dict]]:
    """
    Run both baseline and robust simulations.
    
    Args:
        icc: Intraclass correlation coefficient
        n_iterations: Number of simulation iterations
        seed: Random seed
        n_clusters: Number of clusters
        n_obs_per_cluster: Observations per cluster
        n_permutations: Number of permutations for block permutation test
    
    Returns:
        Tuple of (baseline_results, robust_results)
    """
    logger.info(f"Starting full simulation for ICC={icc}, iterations={n_iterations}")
    
    # Start memory tracing
    tracemalloc.start()
    
    baseline_results = run_baseline_simulation(icc, n_iterations, seed, n_clusters, n_obs_per_cluster)
    robust_results = run_robust_simulation(icc, n_iterations, seed, n_clusters, n_obs_per_cluster, n_permutations)
    
    # Log final memory stats
    current, peak = tracemalloc.get_traced_memory()
    logger.info(f"Simulation complete. Current: {current/1024**2:.2f}MB, Peak: {peak/1024**2:.2f}MB")
    tracemalloc.stop()
    
    return baseline_results, robust_results

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Run A/B test simulation with memory optimization')
    parser.add_argument('--icc', type=float, default=0.1, help='Intraclass correlation coefficient')
    parser.add_argument('--iterations', type=int, default=100, help='Number of simulation iterations')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--n-clusters', type=int, default=100, help='Number of clusters')
    parser.add_argument('--n-obs-per-cluster', type=int, default=50, help='Observations per cluster')
    parser.add_argument('--icc-range', type=str, default=None, help='Comma-separated ICC range (e.g., 0.0,0.1,0.2)')
    parser.add_argument('--icc-step', type=float, default=0.1, help='Step size for ICC range')
    parser.add_argument('--n-permutations', type=int, default=1000, help='Number of permutations for block permutation test')
    parser.add_argument('--output-baseline', type=str, default='data/derived/baseline_results.csv', help='Output path for baseline results')
    parser.add_argument('--output-robust', type=str, default='data/derived/robustResults.csv', help='Output path for robust results')
    
    return parser.parse_args()

def main():
    """Main entry point for the simulation runner."""
    args = parse_args()
    
    # Load and validate config
    cfg = load_config()
    cfg = parse_cli_args(args, cfg)
    validate_config(cfg)
    
    # Determine ICC range
    if args.icc_range:
        icc_values = [float(x) for x in args.icc_range.split(',')]
    else:
        icc_values = [args.icc]
    
    # Ensure output directories exist
    os.makedirs(os.path.dirname(args.output_baseline), exist_ok=True)
    os.makedirs(os.path.dirname(args.output_robust), exist_ok=True)
    
    all_baseline_results = []
    all_robust_results = []
    
    for icc in icc_values:
        logger.info(f"Running simulation for ICC={icc}")
        
        baseline_results, robust_results = run_full_simulation(
            icc=icc,
            n_iterations=args.iterations,
            seed=args.seed,
            n_clusters=args.n_clusters,
            n_obs_per_cluster=args.n_obs_per_cluster,
            n_permutations=args.n_permutations
        )
        
        all_baseline_results.extend(baseline_results)
        all_robust_results.extend(robust_results)
    
    # Write baseline results
    if all_baseline_results:
        df_baseline = pd.DataFrame(all_baseline_results)
        df_baseline.to_csv(args.output_baseline, index=False)
        logger.info(f"Wrote {len(all_baseline_results)} baseline results to {args.output_baseline}")
    else:
        logger.warning("No baseline results to write")
        pd.DataFrame(columns=['iteration', 'icc', 'p_value', 'method', 'n_clusters', 'n_obs_per_cluster']).to_csv(args.output_baseline, index=False)
    
    # Write robust results
    if all_robust_results:
        df_robust = pd.DataFrame(all_robust_results)
        df_robust.to_csv(args.output_robust, index=False)
        logger.info(f"Wrote {len(all_robust_results)} robust results to {args.output_robust}")
    else:
        logger.warning("No robust results to write")
        pd.DataFrame(columns=['iteration', 'icc', 'p_value', 'method', 'n_clusters', 'n_obs_per_cluster']).to_csv(args.output_robust, index=False)
    
    logger.info("Simulation complete")

if __name__ == '__main__':
    main()