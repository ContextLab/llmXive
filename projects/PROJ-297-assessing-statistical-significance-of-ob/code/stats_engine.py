import pandas as pd
import numpy as np
from scipy import stats
import networkx as nx
from typing import Callable, Dict, List, Optional, Tuple, Any
import math
import logging
import time
from config import get_config

CONFIG = get_config()
logger = logging.getLogger(__name__)

def compute_correlation(df: pd.DataFrame, method: str = 'pearson') -> pd.DataFrame:
    """Compute correlation matrix."""
    return df.corr(method=method)

def construct_graph(corr_matrix: pd.DataFrame, threshold: float) -> nx.Graph:
    """Construct graph from correlation matrix with threshold."""
    G = nx.Graph()
    variables = corr_matrix.columns
    G.add_nodes_from(variables)
    
    # Add edges where |corr| > threshold
    for i in range(len(variables)):
        for j in range(i + 1, len(variables)):
            val = abs(corr_matrix.iloc[i, j])
            if val > threshold:
                G.add_edge(variables[i], variables[j], weight=val)
    return G

def calculate_stats(graph: nx.Graph) -> Dict[str, float]:
    """Calculate network statistics."""
    stats = {}
    stats['edge_density'] = nx.density(graph)
    
    # Clustering coefficient (handle disconnected graphs)
    if len(graph.nodes()) > 0:
        try:
            stats['average_clustering'] = nx.average_clustering(graph)
        except:
            stats['average_clustering'] = 0.0
    else:
        stats['average_clustering'] = 0.0
        
    # Mean Absolute Correlation (from graph edges if exists, else 0)
    if len(graph.edges()) > 0:
        weights = [data['weight'] for u, v, data in graph.edges(data=True)]
        stats['mean_abs_corr'] = np.mean(weights)
        stats['max_abs_corr'] = np.max(weights)
    else:
        stats['mean_abs_corr'] = 0.0
        stats['max_abs_corr'] = 0.0
        
    return stats

def generate_synthetic_dataset(n: int = 500, v: int = 20, seed: int = 42) -> pd.DataFrame:
    """Generate synthetic dataset with identity covariance (no correlation)."""
    rng = np.random.default_rng(seed)
    data = rng.standard_normal((n, v))
    cols = [f'var_{i}' for i in range(v)]
    return pd.DataFrame(data, columns=cols)

def run_permutations_for_threshold(
    df: pd.DataFrame, 
    threshold: float, 
    n_permutations: int, 
    stats_list: List[str]
) -> Tuple[Dict[str, List[float]], Dict[str, float]]:
    """
    Run permutation engine for a specific threshold.
    Returns null distributions and observed values for requested stats.
    """
    logger.info(f"Running {n_permutations} permutations for threshold {threshold}")
    
    # Compute Observed
    obs_corr = compute_correlation(df, 'pearson')
    obs_graph = construct_graph(obs_corr, threshold)
    obs_stats = calculate_stats(obs_graph)
    
    observed_vals = {s: obs_stats.get(s, 0.0) for s in stats_list}
    
    # Initialize null distributions
    null_dists = {s: [] for s in stats_list}
    
    rng = np.random.default_rng(CONFIG['random_seed'])
    
    for i in range(n_permutations):
        # Permute rows
        perm_df = df.sample(frac=1, random_state=rng).reset_index(drop=True)
        
        # Compute permuted stats
        perm_corr = compute_correlation(perm_df, 'pearson')
        perm_graph = construct_graph(perm_corr, threshold)
        perm_stats = calculate_stats(perm_graph)
        
        for s in stats_list:
            val = perm_stats.get(s, 0.0)
            null_dists[s].append(val)
        
        # Memory cleanup (T086)
        del perm_df, perm_corr, perm_graph, perm_stats
    
    return null_dists, observed_vals

def calculate_empirical_p_value(null_dist: List[float], observed: float) -> float:
    """Calculate empirical p-value: (r+1)/(N+1)."""
    if not null_dist:
        return 1.0
    r = sum(1 for x in null_dist if x >= observed)
    n = len(null_dist)
    return (r + 1) / (n + 1)

def estimate_runtime_pilot(datasets: Dict[str, pd.DataFrame], pilot_n: int = 10) -> int:
    """
    Estimate runtime and determine N.
    T061: Run pilot, estimate time, adjust N to fit 6h budget.
    """
    logger.info("Running pilot to estimate runtime...")
    start = time.time()
    
    # Run pilot on first dataset
    if not datasets:
        return 1000
    sample_id = list(datasets.keys())[0]
    df = datasets[sample_id]
    
    # Run pilot
    run_permutations_for_threshold(df, 0.3, pilot_n, ['edge_density'])
    
    elapsed = time.time() - start
    time_per_perm = elapsed / pilot_n
    
    # Estimate total time for all datasets and thresholds
    # T061: 6 hours = 21600 seconds
    num_datasets = len(datasets)
    num_thresholds = 5 # Default sweep size
    total_perms_budget = 21600 / time_per_perm if time_per_perm > 0 else 100000
    
    # N per threshold per dataset
    # total_perms = num_datasets * num_thresholds * N
    # N = total_perms_budget / (num_datasets * num_thresholds)
    estimated_n = int(total_perms_budget / (num_datasets * num_thresholds))
    
    # Enforce bounds (T061)
    min_n_clustering = 100
    min_n_other = 500
    
    # We assume we run clustering, so use min 100.
    # But T061 says "reduce N for Average Clustering Coefficient to 500... then globally".
    # Let's use a global min of 100 for safety in this implementation.
    if estimated_n < 100:
        estimated_n = 100
        logger.warning(f"Estimated N ({estimated_n}) below minimum. Setting to 100.")
    
    logger.info(f"Adaptive N set to {estimated_n} based on pilot.")
    return estimated_n

def adjust_permutation_count(n: int, dataset_size: int) -> int:
    """Adjust N if dataset is small (T083)."""
    # Max permutations = n! (theoretical)
    # Practical limit: if n < 50, cap N to avoid redundancy?
    # T083: "adjust N dynamically if n < 50"
    if dataset_size < 50:
        max_perm = math.factorial(dataset_size)
        if n > max_perm:
            n = max_perm
    return n

def main():
    # Simple test
    df = generate_synthetic_dataset(100, 10)
    corr = compute_correlation(df)
    print(corr)

if __name__ == '__main__':
    main()
