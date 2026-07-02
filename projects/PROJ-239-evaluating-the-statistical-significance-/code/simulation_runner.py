import warnings
import time
import tracemalloc
import os
import sys
from typing import List, Dict, Union, Optional
import numpy as np
import pandas as pd

from code.config import load_config, set_seed, validate_config
from code.data_generator import generate_data
from code.estimators import run_naive_ttest_with_warning, run_cluster_robust_ttest, run_block_permutation
from code.analysis import aggregate_errors

# Memory constraints (in GB)
MEMORY_THRESHOLD_GB = 6.0
MAX_MEMORY_GB = 7.0
BYTES_PER_OBS_ESTIMATE = 200  # Conservative estimate per row (floats + overhead)

def estimate_memory_footprint(n_clusters: int, n_obs_per_cluster: int) -> float:
    """
    Estimate the memory footprint of the simulation data in GB.
    
    Args:
        n_clusters: Number of clusters.
        n_obs_per_cluster: Number of observations per cluster.
        
    Returns:
        Estimated memory usage in GB.
    """
    total_obs = n_clusters * n_obs_per_cluster
    estimated_bytes = total_obs * BYTES_PER_OBS_ESTIMATE
    return estimated_bytes / (1024 ** 3)

def downsample_clusters(
    n_clusters: int, 
    current_n_obs: int, 
    target_memory_gb: float
) -> int:
    """
    Calculate the maximum number of observations per cluster to stay under target memory.
    
    Args:
        n_clusters: Number of clusters.
        current_n_obs: Current observations per cluster (before downsampling).
        target_memory_gb: Target memory limit in GB.
        
    Returns:
        New number of observations per cluster (integer >= 1).
    """
    max_total_obs = int((target_memory_gb * (1024 ** 3)) / BYTES_PER_OBS_ESTIMATE)
    new_n_obs = max(1, max_total_obs // n_clusters)
    return new_n_obs

def run_baseline_simulation(
    icc: float, 
    n_iterations: int, 
    seed: int,
    n_clusters: Optional[int] = None,
    n_obs_per_cluster: Optional[int] = None,
    alpha_levels: Optional[List[float]] = None
) -> List[Dict]:
    """
    Run the baseline simulation (naive t-test) with memory optimization.
    
    If the estimated memory footprint exceeds MEMORY_THRESHOLD_GB, observations
    per cluster are downsampled to keep total usage below MAX_MEMORY_GB.
    
    Args:
        icc: Intra-cluster correlation coefficient.
        n_iterations: Number of simulation iterations.
        seed: Random seed.
        n_clusters: Number of clusters (optional, uses config default if None).
        n_obs_per_cluster: Observations per cluster (optional, uses config default if None).
        alpha_levels: List of alpha levels for error rate calculation.
        
    Returns:
        List of dictionaries containing simulation results.
    """
    # Load config if not provided
    if n_clusters is None or n_obs_per_cluster is None:
        cfg = load_config()
        n_clusters = n_clusters or cfg.get('n_clusters', 100)
        n_obs_per_cluster = n_obs_per_cluster or cfg.get('n_obs_per_cluster', 20)
        alpha_levels = alpha_levels or cfg.get('alpha_levels', [0.01, 0.05, 0.10])
    
    # Memory optimization check
    initial_footprint = estimate_memory_footprint(n_clusters, n_obs_per_cluster)
    
    if initial_footprint > MEMORY_THRESHOLD_GB:
        warnings.warn(
            f"Estimated memory footprint ({initial_footprint:.2f} GB) exceeds "
            f"threshold ({MEMORY_THRESHOLD_GB} GB). Downsampling observations per cluster.",
            UserWarning
        )
        new_n_obs = downsample_clusters(n_clusters, n_obs_per_cluster, MAX_MEMORY_GB)
        warnings.warn(
            f"Reduced observations per cluster from {n_obs_per_cluster} to {new_n_obs} "
            f"to stay under {MAX_MEMORY_GB} GB limit."
        )
        n_obs_per_cluster = new_n_obs

    results = []
    
    for i in range(n_iterations):
        # Set seed for this iteration
        iteration_seed = seed + i
        set_seed(iteration_seed)
        
        # Generate data
        data = generate_data(
            n_clusters=n_clusters,
            n_obs_per_cluster=n_obs_per_cluster,
            icc=icc,
            seed=iteration_seed
        )
        
        # Run naive t-test
        p_value = run_naive_ttest_with_warning(data, 'treatment', 'outcome')
        
        results.append({
            'iteration': i,
            'icc': icc,
            'p_value_naive': p_value,
            'n_clusters': n_clusters,
            'n_obs_per_cluster': n_obs_per_cluster,
            'method': 'naive_ttest'
        })
        
        # Progress indicator
        if (i + 1) % 100 == 0:
            print(f"Completed {i + 1}/{n_iterations} iterations for ICC={icc}")
    
    return results

def run_robust_simulation(
    icc: float,
    n_iterations: int,
    seed: int,
    n_clusters: Optional[int] = None,
    n_obs_per_cluster: Optional[int] = None,
    alpha_levels: Optional[List[float]] = None,
    n_permutations: int = 1000
) -> List[Dict]:
    """
    Run the robust simulation (cluster-robust t-test and block permutation) 
    with memory optimization.
    
    Args:
        icc: Intra-cluster correlation coefficient.
        n_iterations: Number of simulation iterations.
        seed: Random seed.
        n_clusters: Number of clusters (optional, uses config default if None).
        n_obs_per_cluster: Observations per cluster (optional, uses config default if None).
        alpha_levels: List of alpha levels for error rate calculation.
        n_permutations: Number of permutations for block permutation test.
        
    Returns:
        List of dictionaries containing simulation results for all methods.
    """
    # Load config if not provided
    if n_clusters is None or n_obs_per_cluster is None:
        cfg = load_config()
        n_clusters = n_clusters or cfg.get('n_clusters', 100)
        n_obs_per_cluster = n_obs_per_cluster or cfg.get('n_obs_per_cluster', 20)
        alpha_levels = alpha_levels or cfg.get('alpha_levels', [0.01, 0.05, 0.10])
    
    # Memory optimization check
    initial_footprint = estimate_memory_footprint(n_clusters, n_obs_per_cluster)
    
    if initial_footprint > MEMORY_THRESHOLD_GB:
        warnings.warn(
            f"Estimated memory footprint ({initial_footprint:.2f} GB) exceeds "
            f"threshold ({MEMORY_THRESHOLD_GB} GB). Downsampling observations per cluster.",
            UserWarning
        )
        new_n_obs = downsample_clusters(n_clusters, n_obs_per_cluster, MAX_MEMORY_GB)
        warnings.warn(
            f"Reduced observations per cluster from {n_obs_per_cluster} to {new_n_obs} "
            f"to stay under {MAX_MEMORY_GB} GB limit."
        )
        n_obs_per_cluster = new_n_obs

    results = []
    
    for i in range(n_iterations):
        # Set seed for this iteration
        iteration_seed = seed + i
        set_seed(iteration_seed)
        
        # Generate data
        data = generate_data(
            n_clusters=n_clusters,
            n_obs_per_cluster=n_obs_per_cluster,
            icc=icc,
            seed=iteration_seed
        )
        
        # Run naive t-test
        p_naive = run_naive_ttest_with_warning(data, 'treatment', 'outcome')
        
        # Run cluster-robust t-test
        p_robust = run_cluster_robust_ttest(data, 'treatment', 'outcome', 'cluster_id')
        
        # Run block permutation test
        p_perm = run_block_permutation(data, 'treatment', 'outcome', 'cluster_id', n_permutations)
        
        results.append({
            'iteration': i,
            'icc': icc,
            'p_value_naive': p_naive,
            'p_value_robust': p_robust,
            'p_value_permutation': p_perm,
            'n_clusters': n_clusters,
            'n_obs_per_cluster': n_obs_per_cluster,
            'method': 'all'
        })
        
        # Progress indicator
        if (i + 1) % 100 == 0:
            print(f"Completed {i + 1}/{n_iterations} iterations for ICC={icc}")
    
    return results

def run_full_simulation(
    icc_range: List[float],
    n_iterations: int,
    seed: int,
    n_clusters: Optional[int] = None,
    n_obs_per_cluster: Optional[int] = None,
    alpha_levels: Optional[List[float]] = None,
    n_permutations: int = 1000,
    run_baseline: bool = True,
    run_robust: bool = True
) -> Dict[str, pd.DataFrame]:
    """
    Run simulations across a range of ICC values with memory optimization.
    
    Args:
        icc_range: List of ICC values to test.
        n_iterations: Number of iterations per ICC.
        seed: Random seed.
        n_clusters: Number of clusters (optional).
        n_obs_per_cluster: Observations per cluster (optional).
        alpha_levels: List of alpha levels (optional).
        n_permutations: Number of permutations for block test.
        run_baseline: Whether to run baseline simulation.
        run_robust: Whether to run robust simulation.
        
    Returns:
        Dictionary with keys 'baseline' and/or 'robust' containing DataFrames.
    """
    results_dict = {}
    
    for icc in icc_range:
        print(f"Starting simulation for ICC={icc}")
        
        if run_baseline:
            baseline_results = run_baseline_simulation(
                icc=icc,
                n_iterations=n_iterations,
                seed=seed,
                n_clusters=n_clusters,
                n_obs_per_cluster=n_obs_per_cluster,
                alpha_levels=alpha_levels
            )
            if 'baseline' not in results_dict:
                results_dict['baseline'] = []
            results_dict['baseline'].extend(baseline_results)
        
        if run_robust:
            robust_results = run_robust_simulation(
                icc=icc,
                n_iterations=n_iterations,
                seed=seed,
                n_clusters=n_clusters,
                n_obs_per_cluster=n_obs_per_cluster,
                alpha_levels=alpha_levels,
                n_permutations=n_permutations
            )
            if 'robust' not in results_dict:
                results_dict['robust'] = []
            results_dict['robust'].extend(robust_results)
    
    # Convert to DataFrames
    output = {}
    for key, data in results_dict.items():
        output[key] = pd.DataFrame(data)
    
    return output