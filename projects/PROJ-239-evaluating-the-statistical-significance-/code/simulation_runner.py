"""
Simulation runner for A/B test significance evaluation.
Handles baseline and robust simulation loops with memory/time constraints.
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
from code.config import (
    load_config, parse_cli_args, validate_config, set_seed,
    DEFAULT_N_CLUSTERS, DEFAULT_SEED, MEMORY_LIMIT_GB, MIN_CLUSTERS_FOR_ROBUST
)
from code.data_generator import generate_data
from code.estimators import run_naive_ttest_with_warning, run_cluster_robust_ttest, run_block_permutation
from code.analysis import aggregate_errors

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

def estimate_memory_footprint(n_clusters: int, n_obs_per_cluster: int, icc: float) -> float:
    """
    Estimates memory footprint in MB for a given simulation configuration.
    Based on: DataFrame with ~ (n_clusters * n_obs_per_cluster) rows.
    Each row has ~10 columns, float64 (8 bytes).
    Overhead factor of 2 for pandas internal structures.
    """
    total_obs = n_clusters * n_obs_per_cluster
    bytes_per_row = 10 * 8  # 10 columns, 8 bytes each
    estimated_bytes = total_obs * bytes_per_row * 2  # Overhead
    estimated_mb = estimated_bytes / (1024 * 1024)
    
    # Add overhead for random effects generation
    estimated_mb += n_clusters * 10  # Per-cluster random effects
    
    return estimated_mb

def downsample_clusters(n_clusters: int, n_obs_per_cluster: int, target_mb: float = 7000.0) -> Tuple[int, int]:
    """
    Attempts to downsample to meet memory target.
    Returns (new_n_clusters, new_n_obs_per_cluster).
    Raises RuntimeError if downsampling violates statistical validity.
    """
    # Retry 1: Halve n_obs_per_cluster
    new_n_obs = n_obs_per_cluster // 2
    if new_n_obs < 1:
        new_n_obs = 1
    
    mem = estimate_memory_footprint(n_clusters, new_n_obs, 0.0)
    if mem <= target_mb:
        return n_clusters, new_n_obs
    
    # Retry 2: Halve n_clusters
    new_n_clusters = n_clusters // 2
    if new_n_clusters < MIN_CLUSTERS_FOR_ROBUST:
        raise RuntimeError(f"Memory limit exceeded: 7GB. Down-sampling would violate statistical validity (n_clusters < {MIN_CLUSTERS_FOR_ROBUST}).")
    
    mem = estimate_memory_footprint(new_n_clusters, new_n_obs, 0.0)
    if mem <= target_mb:
        return new_n_clusters, new_n_obs
    
    # Retry 3: Further reduce if possible but >= MIN_CLUSTERS
    new_n_clusters = max(MIN_CLUSTERS_FOR_ROBUST, new_n_clusters // 2)
    mem = estimate_memory_footprint(new_n_clusters, new_n_obs, 0.0)
    if mem <= target_mb:
        return new_n_clusters, new_n_obs
    
    raise RuntimeError("Memory limit exceeded: 7GB. Down-sampling failed.")

def log_timing(duration_sec: float, timestamp: str) -> None:
    """Logs timing data to data/timing.csv."""
    os.makedirs('data', exist_ok=True)
    file_path = 'data/timing.csv'
    file_exists = os.path.exists(file_path)
    
    with open(file_path, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'duration_sec'])
        writer.writerow([timestamp, duration_sec])

def log_memory(peak_memory_gb: float, timestamp: str) -> None:
    """Logs memory data to data/memory.csv."""
    os.makedirs('data', exist_ok=True)
    file_path = 'data/memory.csv'
    file_exists = os.path.exists(file_path)
    
    with open(file_path, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'peak_memory_gb'])
        writer.writerow([timestamp, peak_memory_gb])

def log_config_change(iteration: int, original_n_clusters: int, original_n_obs: int, 
                     actual_n_clusters: int, actual_n_obs: int) -> None:
    """Logs downsampling events to data/derived/simulation_config_log.csv."""
    os.makedirs('data/derived', exist_ok=True)
    file_path = 'data/derived/simulation_config_log.csv'
    file_exists = os.path.exists(file_path)
    
    with open(file_path, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['iteration', 'original_n_clusters', 'original_n_obs_per_cluster', 
                           'actual_n_clusters', 'actual_n_obs_per_cluster'])
        writer.writerow([iteration, original_n_clusters, original_n_obs, actual_n_clusters, actual_n_obs])

def run_baseline_simulation(icc: float, n_iterations: int, seed: int, 
                           n_clusters: int = DEFAULT_N_CLUSTERS, 
                           n_obs_per_cluster: int = 12) -> List[Dict[str, Any]]:
    """
    Runs the baseline simulation loop for a single ICC value.
    
    Args:
        icc: Intra-cluster correlation coefficient
        n_iterations: Number of simulation iterations
        seed: Random seed
        n_clusters: Number of clusters
        n_obs_per_cluster: Average observations per cluster
    
    Returns:
        List of result dictionaries with iteration, icc, p_value, rejected
    """
    results = []
    set_seed(seed)
    
    for i in range(n_iterations):
        try:
            # Generate data
            data = generate_data(
                n_clusters=n_clusters,
                n_obs_per_cluster=n_obs_per_cluster,
                icc=icc,
                seed=seed + i
            )
            
            if data is None or len(data) == 0:
                logger.warning(f"Iteration {i}: Data generation failed or empty. Skipping.")
                continue
            
            # Run naive t-test (with warning wrapper)
            p_value = run_naive_ttest_with_warning(
                data, 
                treatment_col='treatment', 
                outcome_col='outcome'
            )
            
            # Determine rejection (default alpha = 0.05, but we'll handle aggregation later)
            rejected = p_value < 0.05
            
            results.append({
                'iteration': i,
                'icc': icc,
                'p_value': p_value,
                'rejected': rejected,
                'n_clusters': n_clusters,
                'n_obs_per_cluster': n_obs_per_cluster
            })
            
        except Exception as e:
            logger.warning(f"Iteration {i} failed: {str(e)}. Skipping.")
            continue
    
    return results

def run_robust_simulation(icc: float, n_iterations: int, seed: int,
                         n_clusters: int = DEFAULT_N_CLUSTERS,
                         n_obs_per_cluster: int = 12) -> List[Dict[str, Any]]:
    """
    Runs the robust simulation loop for a single ICC value.
    Includes cluster-robust t-test and block permutation test.
    """
    results = []
    set_seed(seed)
    
    for i in range(n_iterations):
        try:
            # Generate data
            data = generate_data(
                n_clusters=n_clusters,
                n_obs_per_cluster=n_obs_per_cluster,
                icc=icc,
                seed=seed + i
            )
            
            if data is None or len(data) == 0:
                logger.warning(f"Iteration {i}: Data generation failed or empty. Skipping.")
                continue
            
            # Run cluster-robust t-test
            try:
                p_robust = run_cluster_robust_ttest(
                    data,
                    treatment_col='treatment',
                    outcome_col='outcome',
                    cluster_id_col='cluster_id'
                )
            except Exception as e:
                logger.warning(f"Iteration {i}: Cluster-robust test failed: {e}. Skipping robust.")
                p_robust = np.nan
            
            # Run block permutation test
            try:
                p_perm = run_block_permutation(
                    data,
                    treatment_col='treatment',
                    outcome_col='outcome',
                    cluster_id_col='cluster_id',
                    n_permutations=1000
                )
            except Exception as e:
                logger.warning(f"Iteration {i}: Permutation test failed: {e}. Skipping perm.")
                p_perm = np.nan
            
            # Store results
            results.append({
                'iteration': i,
                'icc': icc,
                'method': 'cluster_robust',
                'p_value': p_robust,
                'rejected': p_robust < 0.05 if not np.isnan(p_robust) else None,
                'n_clusters': n_clusters,
                'n_obs_per_cluster': n_obs_per_cluster
            })
            
            results.append({
                'iteration': i,
                'icc': icc,
                'method': 'block_permutation',
                'p_value': p_perm,
                'rejected': p_perm < 0.05 if not np.isnan(p_perm) else None,
                'n_clusters': n_clusters,
                'n_obs_per_cluster': n_obs_per_cluster
            })
            
        except Exception as e:
            logger.warning(f"Iteration {i} failed: {str(e)}. Skipping.")
            continue
    
    return results

def run_full_simulation(cfg: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Runs the full simulation across all ICC values and methods.
    Implements memory and time constraints (T027).
    
    Returns:
        Tuple of (all_results, performance_metrics)
    """
    icc_range = cfg['icc_range']
    n_iterations = cfg['n_iterations']
    seed = cfg['seed']
    method = cfg.get('method', 'full')
    base_n_clusters = cfg['n_clusters']
    base_n_obs = cfg['n_obs_per_cluster']
    
    start_time = time.time()
    tracemalloc.start()
    
    all_results = []
    performance_metrics = {
        'total_time_sec': 0,
        'peak_memory_gb': 0,
        'iterations_completed': 0,
        'status': 'success',
        'downsampling_events': []
    }
    
    time_limit = 21600  # 6 hours
    
    for icc in icc_range:
        # Check time limit
        elapsed = time.time() - start_time
        if elapsed > time_limit:
            performance_metrics['status'] = 'timeout'
            performance_metrics['total_time_sec'] = elapsed
            logger.error("Time limit exceeded: 6 hours.")
            break
        
        # Estimate memory and downsample if needed
        est_mem = estimate_memory_footprint(base_n_clusters, base_n_obs, icc)
        current_n_clusters = base_n_clusters
        current_n_obs = base_n_obs
        downsampling_occurred = False
        
        if est_mem > 7000:  # 7GB in MB
            logger.info(f"ICC={icc}: Estimated memory {est_mem:.1f}MB exceeds 7GB limit. Downsampling...")
            try:
                current_n_clusters, current_n_obs = downsample_clusters(base_n_clusters, base_n_obs)
                downsampling_occurred = True
                log_config_change(0, base_n_clusters, base_n_obs, current_n_clusters, current_n_obs)
                logger.info(f"ICC={icc}: Downsampling to n_clusters={current_n_clusters}, n_obs={current_n_obs}")
            except RuntimeError as e:
                logger.error(f"ICC={icc}: {str(e)}")
                performance_metrics['status'] = 'memory_error'
                break
        
        if method in ['baseline', 'full']:
            logger.info(f"Running baseline simulation for ICC={icc}")
            baseline_results = run_baseline_simulation(
                icc=icc,
                n_iterations=n_iterations,
                seed=seed,
                n_clusters=current_n_clusters,
                n_obs_per_cluster=current_n_obs
            )
            all_results.extend(baseline_results)
            performance_metrics['iterations_completed'] += len(baseline_results)
        
        if method in ['robust', 'full']:
            logger.info(f"Running robust simulation for ICC={icc}")
            robust_results = run_robust_simulation(
                icc=icc,
                n_iterations=n_iterations,
                seed=seed,
                n_clusters=current_n_clusters,
                n_obs_per_cluster=current_n_obs
            )
            all_results.extend(robust_results)
            performance_metrics['iterations_completed'] += len(robust_results)
        
        # Log memory
        current, peak = tracemalloc.get_traced_memory()
        peak_gb = peak / (1024 * 1024 * 1024)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_memory(peak_gb, timestamp)
        
        if peak_gb > MEMORY_LIMIT_GB:
            performance_metrics['status'] = 'memory_error'
            logger.error(f"Memory limit exceeded: {peak_gb:.2f}GB > {MEMORY_LIMIT_GB}GB")
            break
    
    # Finalize metrics
    performance_metrics['total_time_sec'] = time.time() - start_time
    performance_metrics['peak_memory_gb'] = peak_gb
    
    tracemalloc.stop()
    
    return all_results, performance_metrics

def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description="A/B Test Simulation Runner")
    parser.add_argument('--icc', type=float, default=None, help='Single ICC value')
    parser.add_argument('--icc-range', type=str, default=None, help='Comma-separated ICC values')
    parser.add_argument('--icc-step', type=float, default=None, help='ICC step size')
    parser.add_argument('--alpha-list', type=str, default=None, help='Comma-separated alpha levels')
    parser.add_argument('--n-clusters', type=int, default=None, help='Number of clusters')
    parser.add_argument('--n-obs-per-cluster', type=int, default=None, help='Observations per cluster')
    parser.add_argument('--n-iterations', type=int, default=100, help='Number of iterations')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--method', type=str, default='full', choices=['baseline', 'robust', 'full'], help='Simulation method')
    parser.add_argument('--output-dir', type=str, default='data/derived', help='Output directory')
    return parser.parse_args(args)

def main():
    """Main entry point for the simulation runner."""
    args = parse_args()
    
    # Load config
    cfg = load_config()
    
    # Override with CLI args
    cli_args = []
    if args.icc is not None:
        cli_args.extend(['--icc', str(args.icc)])
    if args.icc_range:
        cli_args.extend(['--icc-range', args.icc_range])
    if args.icc_step is not None:
        cli_args.extend(['--icc-step', str(args.icc_step)])
    if args.alpha_list:
        cli_args.extend(['--alpha-list', args.alpha_list])
    if args.n_clusters is not None:
        cli_args.extend(['--n-clusters', str(args.n_clusters)])
    if args.n_obs_per_cluster is not None:
        cli_args.extend(['--n-obs-per-cluster', str(args.n_obs_per_cluster)])
    if args.n_iterations is not None:
        cli_args.extend(['--n-iterations', str(args.n_iterations)])
    if args.seed is not None:
        cli_args.extend(['--seed', str(args.seed)])
    if args.method is not None:
        cli_args.extend(['--method', args.method])
    
    cfg = parse_cli_args(cli_args, cfg)
    
    # Ensure output directory exists
    os.makedirs(cfg.get('output_dir', 'data/derived'), exist_ok=True)
    
    logger.info(f"Starting simulation with config: {cfg}")
    
    # Run simulation
    results, metrics = run_full_simulation(cfg)
    
    logger.info(f"Simulation complete. {len(results)} results generated.")
    logger.info(f"Performance: {metrics}")
    
    # Write results to CSV
    if results:
        output_file = os.path.join(cfg.get('output_dir', 'data/derived'), 'simulation_results.csv')
        df = pd.DataFrame(results)
        df.to_csv(output_file, index=False)
        logger.info(f"Results written to {output_file}")
    else:
        logger.warning("No results generated. Output file not created.")
        sys.exit(1)
    
    # Write performance metrics
    metrics_file = os.path.join(cfg.get('output_dir', 'data/derived'), 'performance_summary.csv')
    pd.DataFrame([metrics]).to_csv(metrics_file, index=False)
    logger.info(f"Performance metrics written to {metrics_file}")

if __name__ == '__main__':
    main()