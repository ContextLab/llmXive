import warnings
import time
import tracemalloc
import os
from typing import List, Dict, Union
import numpy as np
import pandas as pd
from code.config import set_seed, load_config
from code.data_generator import generate_data
from code.estimators import (
    run_naive_ttest_with_warning,
    run_cluster_robust_ttest,
    run_block_permutation,
)

MAX_MEMORY_GB = 7.0
MEMORY_THRESHOLD_GB = 6.0

def _check_memory_usage(start_mem: float) -> None:
    current, peak = tracemalloc.get_traced_memory()
    peak_gb = peak / (1024 * 1024 * 1024)
    if peak_gb > MAX_MEMORY_GB:
        raise MemoryError(
            f"Peak memory usage ({peak_gb:.2f} GB) exceeded limit of {MAX_MEMORY_GB} GB. "
            "Consider reducing iterations or cluster sizes."
        )
    return peak_gb

def _estimate_memory_footprint(n_clusters: int, n_obs_per_cluster: int) -> float:
    # Rough estimate: 8 bytes per float64, 2 arrays (outcome, treatment) + overhead
    # Assume ~30 bytes per row for DataFrame overhead
    estimated_bytes = n_clusters * n_obs_per_cluster * 30
    return estimated_bytes / (1024 * 1024 * 1024)

def _maybe_downsample(cfg: Dict) -> Dict:
    n_clusters = cfg.get('n_clusters', 100)
    n_obs = cfg.get('n_obs_per_cluster', 20)
    est_footprint = _estimate_memory_footprint(n_clusters, n_obs)

    if est_footprint > MEMORY_THRESHOLD_GB:
        new_n_obs = int((MEMORY_THRESHOLD_GB / est_footprint) * n_obs)
        if new_n_obs < 2:
            raise ValueError(
                "Cannot reduce observations per cluster below 2 while staying under memory threshold."
            )
        warnings.warn(
            f"Estimated memory footprint ({est_footprint:.2f} GB) exceeds threshold. "
            f"Downsampling observations per cluster from {n_obs} to {new_n_obs}."
        )
        cfg['n_obs_per_cluster'] = new_n_obs
    return cfg

def run_baseline_simulation(
    icc: float,
    n_iterations: int,
    seed: int,
    n_clusters: int = 100,
    n_obs_per_cluster: int = 20,
    alpha_levels: List[float] = None,
) -> List[Dict]:
    """
    Run the baseline simulation for a specific ICC value.
    Logs wall-clock time and memory usage.
    """
    if alpha_levels is None:
        alpha_levels = [0.05]

    set_seed(seed)
    cfg = {
        'icc': icc,
        'n_clusters': n_clusters,
        'n_obs_per_cluster': n_obs_per_cluster,
    }
    cfg = _maybe_downsample(cfg)
    n_clusters = cfg['n_clusters']
    n_obs_per_cluster = cfg['n_obs_per_cluster']

    tracemalloc.start()
    start_time = time.time()

    results = []
    for i in range(n_iterations):
        current_seed = seed + i
        data = generate_data(
            n_clusters=n_clusters,
            n_obs_per_cluster=n_obs_per_cluster,
            icc=icc,
            seed=current_seed,
        )

        p_val = run_naive_ttest_with_warning(
            data,
            treatment_col='treatment',
            outcome_col='outcome',
        )

        results.append({
            'iteration': i,
            'icc': icc,
            'method': 'naive_ttest',
            'p_value': p_val,
            'n_clusters': n_clusters,
            'n_obs_per_cluster': n_obs_per_cluster,
        })

    end_time = time.time()
    elapsed = end_time - start_time
    peak_mem = _check_memory_usage(0)
    tracemalloc.stop()

    timing_path = 'data/timing.csv'
    timing_df = pd.DataFrame([{
        'task': f'baseline_icc_{icc}',
        'n_iterations': n_iterations,
        'elapsed_seconds': elapsed,
        'icc': icc,
    }])
    timing_df.to_csv(timing_path, mode='a', header=not os.path.exists(timing_path), index=False)

    mem_path = 'data/memory.csv'
    mem_df = pd.DataFrame([{
        'task': f'baseline_icc_{icc}',
        'peak_memory_gb': peak_mem,
        'icc': icc,
    }])
    mem_df.to_csv(mem_path, mode='a', header=not os.path.exists(mem_path), index=False)

    print(f"Baseline simulation (ICC={icc}) completed in {elapsed:.2f}s. Peak memory: {peak_mem:.2f} GB.")

    return results

def run_robust_simulation(
    icc: float,
    n_iterations: int,
    seed: int,
    n_clusters: int = 100,
    n_obs_per_cluster: int = 20,
    alpha_levels: List[float] = None,
) -> List[Dict]:
    """
    Run the robust simulation (cluster-robust and block permutation) for a specific ICC value.
    Logs wall-clock time and memory usage.
    """
    if alpha_levels is None:
        alpha_levels = [0.05]

    set_seed(seed)
    cfg = {
        'icc': icc,
        'n_clusters': n_clusters,
        'n_obs_per_cluster': n_obs_per_cluster,
    }
    cfg = _maybe_downsample(cfg)
    n_clusters = cfg['n_clusters']
    n_obs_per_cluster = cfg['n_obs_per_cluster']

    tracemalloc.start()
    start_time = time.time()

    results = []
    for i in range(n_iterations):
        current_seed = seed + i
        data = generate_data(
            n_clusters=n_clusters,
            n_obs_per_cluster=n_obs_per_cluster,
            icc=icc,
            seed=current_seed,
        )

        p_naive = run_naive_ttest_with_warning(
            data,
            treatment_col='treatment',
            outcome_col='outcome',
        )

        p_robust = run_cluster_robust_ttest(
            data,
            treatment_col='treatment',
            outcome_col='outcome',
            cluster_id_col='cluster_id',
        )

        p_perm = run_block_permutation(
            data,
            treatment_col='treatment',
            outcome_col='outcome',
            cluster_id_col='cluster_id',
            n_permutations=min(1000, max(100, n_iterations)),
        )

        results.append({
            'iteration': i,
            'icc': icc,
            'method': 'naive_ttest',
            'p_value': p_naive,
            'n_clusters': n_clusters,
            'n_obs_per_cluster': n_obs_per_cluster,
        })
        results.append({
            'iteration': i,
            'icc': icc,
            'method': 'cluster_robust',
            'p_value': p_robust,
            'n_clusters': n_clusters,
            'n_obs_per_cluster': n_obs_per_cluster,
        })
        results.append({
            'iteration': i,
            'icc': icc,
            'method': 'block_permutation',
            'p_value': p_perm,
            'n_clusters': n_clusters,
            'n_obs_per_cluster': n_obs_per_cluster,
        })

    end_time = time.time()
    elapsed = end_time - start_time
    peak_mem = _check_memory_usage(0)
    tracemalloc.stop()

    timing_path = 'data/timing.csv'
    timing_df = pd.DataFrame([{
        'task': f'robust_icc_{icc}',
        'n_iterations': n_iterations,
        'elapsed_seconds': elapsed,
        'icc': icc,
    }])
    timing_df.to_csv(timing_path, mode='a', header=not os.path.exists(timing_path), index=False)

    mem_path = 'data/memory.csv'
    mem_df = pd.DataFrame([{
        'task': f'robust_icc_{icc}',
        'peak_memory_gb': peak_mem,
        'icc': icc,
    }])
    mem_df.to_csv(mem_path, mode='a', header=not os.path.exists(mem_path), index=False)

    print(f"Robust simulation (ICC={icc}) completed in {elapsed:.2f}s. Peak memory: {peak_mem:.2f} GB.")

    return results
