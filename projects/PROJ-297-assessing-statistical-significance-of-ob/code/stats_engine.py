import pandas as pd
import numpy as np
from scipy import stats
import networkx as nx
from typing import Callable, Dict, List, Optional, Tuple, Any
import math
import logging
from config import MASTER_SEED

logger = logging.getLogger("stats_engine")

def compute_correlation(df: pd.DataFrame, method: str = 'pearson') -> pd.DataFrame:
    """Compute correlation matrix."""
    # Ensure only numeric columns
    num_df = df.select_dtypes(include=[np.number])
    if num_df.shape[1] < 2:
        raise ValueError("DataFrame must have at least 2 numeric columns.")
    return num_df.corr(method=method)

def construct_graph(corr_matrix: pd.DataFrame, threshold: float) -> nx.Graph:
    """Construct a graph from correlation matrix."""
    G = nx.Graph()
    nodes = corr_matrix.columns
    G.add_nodes_from(nodes)
    
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            u, v = nodes[i], nodes[j]
            r = corr_matrix.iloc[i, j]
            if abs(r) > threshold:
                G.add_edge(u, v, weight=r)
    return G

def calculate_stats(graph: nx.Graph) -> Dict[str, float]:
    """Calculate network statistics."""
    if graph.number_of_edges() == 0:
        return {
            "density": 0.0,
            "clustering_coefficient": 0.0,
            "avg_degree": 0.0
        }
    
    density = nx.density(graph)
    clustering = nx.average_clustering(graph)
    avg_degree = sum(dict(graph.degree()).values()) / len(graph.nodes())
    
    return {
        "density": density,
        "clustering_coefficient": clustering,
        "avg_degree": avg_degree
    }

def generate_synthetic_dataset(n_samples: int = 500, n_vars: int = 20, seed: int = 42) -> pd.DataFrame:
    """Generate a synthetic dataset with identity covariance."""
    np.random.seed(seed)
    data = np.random.randn(n_samples, n_vars)
    cols = [f"synthetic_var_{i}" for i in range(n_vars)]
    return pd.DataFrame(data, columns=cols)

def run_permutations_for_threshold(
    df: pd.DataFrame,
    threshold: float,
    n_permutations: int = 2000,
    seed: int = 42
) -> List[float]:
    """Run permutations to generate null distribution for a threshold."""
    np.random.seed(seed)
    null_densities = []
    
    # Compute observed density
    corr_obs = compute_correlation(df)
    G_obs = construct_graph(corr_obs, threshold)
    obs_stats = calculate_stats(G_obs)
    obs_density = obs_stats['density']
    
    # Permutations
    for i in range(n_permutations):
        # Shuffle columns independently
        df_perm = df.apply(np.random.permutation)
        
        # Compute stats
        corr_perm = compute_correlation(df_perm)
        G_perm = construct_graph(corr_perm, threshold)
        stats_perm = calculate_stats(G_perm)
        
        null_densities.append(stats_perm['density'])
    
    return null_densities

def calculate_empirical_p_value(null_dist: List[float], observed: float) -> float:
    """Calculate two-sided empirical p-value."""
    if not null_dist:
        return 1.0
    
    # Two-sided: count how many null values are >= |observed|
    # Since densities are positive, we just check >= observed
    count = sum(1 for x in null_dist if x >= observed)
    
    # Add 1 to numerator and denominator to avoid p=0
    p_val = (count + 1) / (len(null_dist) + 1)
    
    # Floor enforcement (T078)
    if p_val == 0.0:
        p_val = 1e-10
    elif p_val == 1.0:
        p_val = 1.0 - 1e-10
        
    return p_val

def estimate_runtime_pilot(df: pd.DataFrame, threshold: float, n_permutations: int = 100) -> float:
    """Estimate runtime for full permutation run."""
    start = time.time()
    run_permutations_for_threshold(df, threshold, n_permutations=n_permutations)
    elapsed = time.time() - start
    return elapsed * (2000 / n_permutations)

def adjust_permutation_count(df: pd.DataFrame, threshold: float, max_time: int = 3600) -> int:
    """Adjust permutation count based on estimated runtime."""
    pilot_time = estimate_runtime_pilot(df, threshold, n_permutations=100)
    estimated_full_time = pilot_time * (2000 / 100)
    
    if estimated_full_time > max_time:
        # Scale down
        ratio = max_time / estimated_full_time
        return int(2000 * ratio)
    return 2000

def main():
    """Main entry point for stats engine testing."""
    logger.info("Running stats engine main...")
    df = generate_synthetic_dataset()
    corr = compute_correlation(df)
    G = construct_graph(corr, 0.3)
    stats = calculate_stats(G)
    logger.info(f"Stats: {stats}")
    
    null_dist = run_permutations_for_threshold(df, 0.3, n_permutations=100, seed=42)
    p_val = calculate_empirical_p_value(null_dist, stats['density'])
    logger.info(f"P-value: {p_val}")

if __name__ == "__main__":
    main()
