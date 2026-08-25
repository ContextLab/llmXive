import pandas as pd
import numpy as np
from scipy import stats
import networkx as nx
from typing import Callable, Dict, List, Optional, Tuple, Any
import math
import logging
from joblib import Parallel, delayed
import psutil

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def compute_correlation(df: pd.DataFrame, method: str = 'pearson') -> pd.DataFrame:
    """Compute the correlation matrix of a DataFrame."""
    return df.corr(method=method)

def construct_graph(corr_matrix: pd.DataFrame, threshold: float) -> nx.Graph:
    """Construct a graph from a correlation matrix above a threshold."""
    G = nx.Graph()
    nodes = corr_matrix.columns
    G.add_nodes_from(nodes)
    
    threshold = float(threshold)
    for i in range(len(nodes)):
        for j in range(i+1, len(nodes)):
            u, v = nodes[i], nodes[j]
            val = corr_matrix.iloc[i, j]
            if abs(val) >= threshold:
                G.add_edge(u, v, weight=val)
    return G

def calculate_stats(graph: nx.Graph) -> Dict[str, Any]:
    """Calculate network statistics for a graph."""
    if graph.number_of_nodes() == 0:
        return {'num_nodes': 0, 'num_edges': 0, 'density': 0.0, 'clustering': 0.0}
    
    return {
        'num_nodes': graph.number_of_nodes(),
        'num_edges': graph.number_of_edges(),
        'density': nx.density(graph),
        'clustering': nx.average_clustering(graph) if graph.number_of_nodes() > 2 else 0.0
    }

def generate_synthetic_dataset(n_samples: int = 500, n_features: int = 20, seed: int = 42) -> pd.DataFrame:
    """Generate a synthetic dataset with identity covariance."""
    np.random.seed(seed)
    data = np.random.randn(n_samples, n_features)
    columns = [f'var_{i}' for i in range(n_features)]
    return pd.DataFrame(data, columns=columns)

def run_permutations_for_threshold(
    df: pd.DataFrame, 
    n_permutations: int, 
    threshold: float, 
    method: str = 'pearson',
    seed: int = 42
) -> Tuple[List[np.ndarray], List[float]]:
    """
    Run permutation tests to generate null distribution for a given threshold.
    Returns (null_distributions, observed_stats).
    """
    np.random.seed(seed)
    corr_matrix = compute_correlation(df, method=method)
    obs_graph = construct_graph(corr_matrix, threshold)
    obs_stat = obs_graph.number_of_edges()
    
    # Parallelize permutations
    def single_permutation(df, n_perm, threshold, method, local_seed):
        np.random.seed(local_seed)
        permuted_df = df.apply(np.random.permutation)
        perm_corr = compute_correlation(permuted_df, method=method)
        perm_graph = construct_graph(perm_corr, threshold)
        return perm_graph.number_of_edges()
    
    # Generate seeds for workers
    worker_seeds = [seed + i for i in range(n_permutations)]
    
    null_stats = Parallel(n_jobs=-1)(
        delayed(single_permutation)(df, n_permutations, threshold, method, s) 
        for s in worker_seeds
    )
    
    return [np.array([s]) for s in null_stats], [obs_stat]

def calculate_empirical_p_value(obs_stat: float, null_dist: np.ndarray) -> float:
    """Calculate two-sided empirical p-value."""
    # Ensure null_dist is a 1D array
    if null_dist.ndim > 1:
        null_dist = null_dist.flatten()
    
    # Avoid p=0 or p=1
    n = len(null_dist)
    count_extreme = np.sum(np.abs(null_dist) >= abs(obs_stat))
    p_val = (count_extreme + 1) / (n + 1)
    return max(min(p_val, 1.0 - 1e-9), 1e-9)

def estimate_runtime_pilot(df: pd.DataFrame, n_permutations: int, threshold: float) -> float:
    """Estimate runtime for a full permutation run."""
    # Run a small pilot
    pilot_n = 10
    start = time.time()
    run_permutations_for_threshold(df, pilot_n, threshold)
    end = time.time()
    return (end - start) / pilot_n * n_permutations

def adjust_permutation_count(runtime_limit: float, estimated_time: float) -> int:
    """Adjust permutation count based on runtime limit."""
    if estimated_time == 0:
        return 2000
    ratio = runtime_limit / estimated_time
    return max(100, min(int(ratio * 2000), 10000))

def main():
    """Main entry point for stats engine (for testing)."""
    pass

import time
if __name__ == "__main__":
    pass
