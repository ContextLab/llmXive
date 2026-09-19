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

# Import from local modules
from code.config import validate_config, load_config, set_seed, parse_cli_args
from code.data_generator import generate_data
from code.estimators import (
    run_naive_ttest_with_warning,
    run_cluster_robust_ttest,
    run_block_permutation
)
from code.analysis import aggregate_errors, select_ci_method

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/simulation.log')
    ]
)
logger = logging.getLogger(__name__)

def estimate_memory_footprint(n_clusters: int, n_obs_per_cluster: int) -> float:
    """
    Estimates memory footprint in MB.
    
    Args:
        n_clusters: Number of clusters.
        n_obs_per_cluster: Number of observations per cluster.
                
    Returns:
        Estimated memory in MB.
    """
    # Rough estimate: 8 bytes per float64, 3 columns (cluster_id, treatment, outcome)
    # Plus overhead for pandas DataFrame
    total_rows = n_clusters * n_obs_per_cluster
    base_size = total_rows * 3 * 8  # 3 columns * 8 bytes
    overhead = base_size * 0.5  # 50% overhead for pandas
    return (base_size + overhead) / (1024 * 1024)

def downsample_clusters(n_clusters: int, n_obs_per_cluster: int, max_mb: float = 7000) -> Tuple[int, int]:
    """
    Down-samples clusters and observations to meet memory constraints.
    
    Args:
        n_clusters: Original number of clusters.
        n_obs_per_cluster: Original number of observations per cluster.
        max_mb: Maximum allowed memory in MB.
                
    Returns:
        Tuple of (new_n_clusters, new_n_obs_per_cluster)
                
    Raises:
        RuntimeError: If down-sampling would violate statistical validity.
    """
    current_clusters = n_clusters
    current_obs = n_obs_per_cluster
    
    # Retry logic
    for retry in range(3):
        estimated_mb = estimate_memory_footprint(current_clusters, current_obs)
        if estimated_mb <= max_mb:
            return current_clusters, current_obs
            
        if retry == 0:
            # First retry: halve observations
            current_obs = max(1, current_obs // 2)
        elif retry == 1:
            # Second retry: halve clusters
            current_clusters = max(1, current_clusters // 2)
        else:
            # Third retry: fail if still too large
            if current_clusters < 50:
                raise RuntimeError("Memory limit exceeded: 7GB. Down-sampling would violate statistical validity (n_clusters < 50).")
            else:
                raise RuntimeError("Memory limit exceeded: 7GB. Down-sampling failed.")
                
    return current_clusters, current_obs

def log_timing(duration_sec: float, output_path: str = 'data/timing.csv') -> None:
    """Logs timing data to CSV."""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    file_exists = os.path.exists(output_path)
    
    with open(output_path, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'duration_sec'])
        writer.writerow([timestamp, duration_sec])

def log_memory(peak_memory_gb: float, output_path: str = 'data/memory.csv') -> None:
    """Logs memory data to CSV."""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    file_exists = os.path.exists(output_path)
    
    with open(output_path, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'peak_memory_gb'])
        writer.writerow([timestamp, peak_memory_gb])

def log_config_change(cfg: Dict[str, Any], output_path: str = 'data/derived/simulation_config_log.csv') -> None:
    """Logs configuration changes to CSV."""
    file_exists = os.path.exists(output_path)
    
    with open(output_path, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'icc', 'n_clusters', 'n_obs_per_cluster', 'iterations', 'seed'])
        writer.writerow([
            time.strftime('%Y-%m-%d %H:%M:%S'),
            cfg.get('icc'),
            cfg.get('n_clusters'),
            cfg.get('n_obs_per_cluster'),
            cfg.get('iterations'),
            cfg.get('seed')
        ])

def run_baseline_simulation(icc: float, n_iterations: int, seed: int, 
                          n_clusters: int = 100, n_obs_per_cluster: int = 10) -> List[Dict]:
    """
    Runs baseline simulation with naive t-test.
    
    Args:
        icc: Intra-cluster correlation coefficient.
        n_iterations: Number of simulation iterations.
        seed: Random seed.
        n_clusters: Number of clusters.
        n_obs_per_cluster: Number of observations per cluster.
                
    Returns:
        List of result dictionaries.
    """
    results = []
    set_seed(seed)
    
    for i in range(n_iterations):
        try:
            data = generate_data(n_clusters, n_obs_per_cluster, icc, seed + i)
            p_value = run_naive_ttest_with_warning(data, 'treatment', 'outcome')
            results.append({
                'iteration': i,
                'icc': icc,
                'p_value': p_value,
                'method': 'naive',
                'rejected': p_value < 0.05  # Default alpha, will be filtered later
            })
        except Exception as e:
            logger.warning(f"Iteration {i} failed: {e}")
            continue
            
    return results

def run_robust_simulation(icc: float, n_iterations: int, seed: int,
                        n_clusters: int = 100, n_obs_per_cluster: int = 10) -> List[Dict]:
    """
    Runs robust simulation with cluster-robust and permutation tests.
    
    Args:
        icc: Intra-cluster correlation coefficient.
        n_iterations: Number of simulation iterations.
        seed: Random seed.
        n_clusters: Number of clusters.
        n_obs_per_cluster: Number of observations per cluster.
                
    Returns:
        List of result dictionaries.
    """
    results = []
    set_seed(seed)
    
    for i in range(n_iterations):
        try:
            data = generate_data(n_clusters, n_obs_per_cluster, icc, seed + i)
            
            # Run cluster-robust t-test
            try:
                p_robust = run_cluster_robust_ttest(data, 'treatment', 'outcome', 'cluster_id')
                results.append({
                    'iteration': i,
                    'icc': icc,
                    'p_value': p_robust,
                    'method': 'cluster_robust',
                    'rejected': p_robust < 0.05
                })
            except Exception as e:
                logger.warning(f"Cluster-robust test failed at iteration {i}: {e}")
                
            # Run block permutation test
            try:
                p_perm = run_block_permutation(data, 'treatment', 'outcome', 'cluster_id', n_permutations=500)
                results.append({
                    'iteration': i,
                    'icc': icc,
                    'p_value': p_perm,
                    'method': 'block_permutation',
                    'rejected': p_perm < 0.05
                })
            except Exception as e:
                logger.warning(f"Block permutation test failed at iteration {i}: {e}")
                
        except Exception as e:
            logger.warning(f"Iteration {i} failed to generate data: {e}")
            continue
            
    return results

def run_full_simulation(cfg: Dict[str, Any]) -> List[Dict]:
    """
    Runs full simulation with all methods.
    
    Args:
        cfg: Configuration dictionary.
                
    Returns:
        List of result dictionaries.
    """
    all_results = []
    
    icc_values = cfg.get('icc_range', [0.0, 0.1, 0.2])
    icc_step = cfg.get('icc_step', 0.1)
    n_iterations = cfg.get('iterations', 100)
    seed = cfg.get('seed', 42)
    n_clusters = cfg.get('n_clusters', 100)
    n_obs_per_cluster = cfg.get('n_obs_per_cluster', 10)
    
    # Check memory constraints
    estimated_mb = estimate_memory_footprint(n_clusters, n_obs_per_cluster)
    if estimated_mb > 7000:
        logger.info(f"Estimated memory {estimated_mb:.2f} MB exceeds 7GB limit. Attempting down-sampling...")
        try:
            n_clusters, n_obs_per_cluster = downsample_clusters(n_clusters, n_obs_per_cluster)
            logger.info(f"Down-sampled to {n_clusters} clusters, {n_obs_per_cluster} obs per cluster")
            log_config_change(cfg, 'data/derived/simulation_config_log.csv')
        except RuntimeError as e:
            logger.error(str(e))
            raise
    
    start_time = time.time()
    tracemalloc.start()
    
    for icc in icc_values:
        logger.info(f"Running simulation for ICC={icc}")
        
        # Run baseline
        baseline_results = run_baseline_simulation(icc, n_iterations, seed, n_clusters, n_obs_per_cluster)
        all_results.extend(baseline_results)
        
        # Run robust methods
        robust_results = run_robust_simulation(icc, n_iterations, seed, n_clusters, n_obs_per_cluster)
        all_results.extend(robust_results)
        
        # Check time limit
        elapsed = time.time() - start_time
        if elapsed > 21600:  # 6 hours
            raise RuntimeError("Time limit exceeded: 6 hours.")
            
        # Log timing
        log_timing(elapsed, 'data/timing.csv')
        
        # Log memory
        current, peak = tracemalloc.get_traced_memory()
        peak_gb = peak / (1024 * 1024 * 1024)
        log_memory(peak_gb, 'data/memory.csv')
        
    tracemalloc.stop()
    return all_results

def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description='Run A/B test simulation with cluster correlation')
    parser.add_argument('--icc', type=float, help='Intra-cluster correlation coefficient')
    parser.add_argument('--icc-range', type=str, help='Comma-separated ICC values')
    parser.add_argument('--icc-step', type=float, help='Step size for ICC range')
    parser.add_argument('--alpha-list', type=str, help='Comma-separated alpha levels')
    parser.add_argument('--n-clusters', type=int, help='Number of clusters')
    parser.add_argument('--n-obs-per-cluster', type=int, help='Number of observations per cluster')
    parser.add_argument('--seed', type=int, help='Random seed')
    parser.add_argument('--iterations', type=int, help='Number of iterations')
    parser.add_argument('--method', type=str, choices=['baseline', 'robust', 'full'], default='full',
                      help='Simulation method (default: full)')
    return parser.parse_args(args)

def main():
    """Main entry point for simulation runner."""
    args = parse_args()
    cfg = load_config()
    
    # Update config with CLI args
    cfg = parse_cli_args(args, cfg)
    
    logger.info(f"Starting simulation with config: {cfg}")
    
    # Run simulation
    if cfg['method'] == 'baseline':
        results = run_baseline_simulation(
            cfg['icc'],
            cfg['iterations'],
            cfg['seed'],
            cfg['n_clusters'],
            cfg['n_obs_per_cluster']
        )
    elif cfg['method'] == 'robust':
        results = run_robust_simulation(
            cfg['icc'],
            cfg['iterations'],
            cfg['seed'],
            cfg['n_clusters'],
            cfg['n_obs_per_cluster']
        )
    else:  # full
        results = run_full_simulation(cfg)
        
    # Write results
    output_path = 'data/derived/robustResults.csv' if cfg['method'] != 'baseline' else 'data/derived/baseline_results.csv'
    if results:
        df = pd.DataFrame(results)
        df.to_csv(output_path, index=False)
        logger.info(f"Wrote {len(results)} results to {output_path}")
        
        # Verify results
        if len(df) == 0:
            raise RuntimeError(f"Results file {output_path} is empty")
    else:
        raise RuntimeError("No results generated")

if __name__ == '__main__':
    main()