"""
Simulation runner module for baseline and robust simulations.
"""

from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
import time
import tracemalloc
import os

from data_generator import generate_data
from estimators import run_naive_ttest_with_warning
from config import DEFAULT_N_CLUSTERS

def estimate_memory_footprint(n_clusters: int, n_obs_per_cluster: int, n_iterations: int) -> float:
    """
    Estimate memory footprint of a simulation run in gigabytes.

    Args:
        n_clusters: Number of clusters
        n_obs_per_cluster: Observations per cluster
        n_iterations: Number of simulation iterations

    Returns:
        float: Estimated memory usage in GB
    """
    # Rough estimate: each observation takes ~40 bytes (float64 + metadata)
    bytes_per_obs = 40
    total_obs = n_clusters * n_obs_per_cluster * n_iterations
    return (total_obs * bytes_per_obs) / (1024 ** 3)

def optimize_memory(n_clusters: int, n_obs_per_cluster: int, n_iterations: int, max_gb: float = 6.0) -> tuple:
    """
    Adjust simulation parameters to stay within memory limits.

    Args:
        n_clusters: Original number of clusters
        n_obs_per_cluster: Original observations per cluster
        n_iterations: Original number of iterations
        max_gb: Maximum allowed memory in GB

    Returns:
        tuple: (adjusted_n_clusters, adjusted_n_obs_per_cluster, adjusted_n_iterations)
    """
    current_footprint = estimate_memory_footprint(n_clusters, n_obs_per_cluster, n_iterations)

    if current_footprint <= max_gb:
        return n_clusters, n_obs_per_cluster, n_iterations

    # Reduce iterations first (most impactful)
    scale_factor = max_gb / current_footprint
    adjusted_iterations = int(n_iterations * scale_factor)

    if adjusted_iterations < 10:
        # If iterations are too low, reduce cluster size
        adjusted_n_obs = max(5, int(n_obs_per_cluster * scale_factor))
        return n_clusters, adjusted_n_obs, 10

    return n_clusters, n_obs_per_cluster, adjusted_iterations

def run_baseline_simulation(icc: float, n_iterations: int, seed: int) -> List[Dict]:
    """
    Run baseline simulation for a single ICC value.

    This simulation uses the naive t-test which assumes independence,
    allowing us to measure Type I error inflation due to clustering.

    Args:
        icc: Intra-cluster correlation value
        n_iterations: Number of simulation iterations
        seed: Random seed for reproducibility

    Returns:
        List[Dict]: List of result dictionaries with keys:
                   - icc: ICC value
                   - p_value: p-value from naive t-test
                   - iteration: iteration number
    """
    results = []

    # Use default parameters from config
    n_clusters = DEFAULT_N_CLUSTERS
    n_obs_per_cluster = 10

    # Adjust for memory if needed
    n_clusters, n_obs_per_cluster, n_iterations = optimize_memory(
        n_clusters, n_obs_per_cluster, n_iterations
    )

    for i in range(n_iterations):
        # Generate data with current seed
        current_seed = seed + i
        data = generate_data(
            n_clusters=n_clusters,
            n_obs_per_cluster=n_obs_per_cluster,
            icc=icc,
            seed=current_seed
        )

        # Run naive t-test (with warning)
        p_value = run_naive_ttest_with_warning(
            data,
            treatment_col='treatment',
            outcome_col='outcome'
        )

        results.append({
            'icc': icc,
            'p_value': p_value,
            'iteration': i
        })

    return results

def run_robust_simulation(icc: float, n_iterations: int, seed: int) -> List[Dict]:
    """
    Run robust simulation for a single ICC value.

    This simulation uses cluster-robust standard errors and block permutation
    to properly account for intra-cluster correlation.

    Args:
        icc: Intra-cluster correlation value
        n_iterations: Number of simulation iterations
        seed: Random seed for reproducibility

    Returns:
        List[Dict]: List of result dictionaries with keys for each method's p-value
    """
    results = []

    n_clusters = DEFAULT_N_CLUSTERS
    n_obs_per_cluster = 10

    n_clusters, n_obs_per_cluster, n_iterations = optimize_memory(
        n_clusters, n_obs_per_cluster, n_iterations
    )

    for i in range(n_iterations):
        current_seed = seed + i
        data = generate_data(
            n_clusters=n_clusters,
            n_obs_per_cluster=n_obs_per_cluster,
            icc=icc,
            seed=current_seed
        )

        from estimators import run_cluster_robust_ttest, run_block_permutation

        p_naive = run_naive_ttest_with_warning(
            data,
            treatment_col='treatment',
            outcome_col='outcome'
        )

        p_robust = run_cluster_robust_ttest(
            data,
            treatment_col='treatment',
            outcome_col='outcome',
            cluster_id_col='cluster_id'
        )

        p_perm = run_block_permutation(
            data,
            treatment_col='treatment',
            outcome_col='outcome',
            cluster_id_col='cluster_id',
            n_permutations=100
        )

        results.append({
            'icc': icc,
            'iteration': i,
            'p_naive': p_naive,
            'p_robust': p_robust,
            'p_perm': p_perm
        })

    return results

def run_full_simulation(icc_values: List[float], n_iterations: int, seed: int) -> Dict[str, List]:
    """
    Run full simulation across multiple ICC values.

    Args:
        icc_values: List of ICC values to test
        n_iterations: Number of iterations per ICC
        seed: Base random seed

    Returns:
        Dict[str, List]: Dictionary with keys 'baseline', 'robust', 'full'
    """
    baseline_results = []
    robust_results = []

    for icc in icc_values:
        baseline_results.extend(run_baseline_simulation(icc, n_iterations, seed))
        robust_results.extend(run_robust_simulation(icc, n_iterations, seed))
        seed += n_iterations

    return {
        'baseline': baseline_results,
        'robust': robust_results
    }
