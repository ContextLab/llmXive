import pandas as pd
import numpy as np
from scipy import stats
import networkx as nx
from typing import Callable, Dict, List, Optional, Tuple, Any
import config

def compute_correlation(df: pd.DataFrame, method: str) -> pd.DataFrame:
    """Compute correlation matrix for the given DataFrame."""
    if method == 'pearson':
        return df.corr(method='pearson')
    elif method == 'spearman':
        return df.corr(method='spearman')
    else:
        raise ValueError(f"Unknown method: {method}")

def construct_graph(corr_matrix: pd.DataFrame, threshold: float) -> nx.Graph:
    """Construct a graph from correlation matrix above a threshold."""
    G = nx.Graph()
    vars = corr_matrix.columns
    G.add_nodes_from(vars)
    
    for i in range(len(vars)):
        for j in range(i + 1, len(vars)):
            v1, v2 = vars[i], vars[j]
            val = corr_matrix.loc[v1, v2]
            if abs(val) > threshold:
                G.add_edge(v1, v2, weight=val)
    return G

def calculate_stats(graph: nx.Graph, df: pd.DataFrame = None) -> dict:
    """Calculate network statistics."""
    if graph.number_of_edges() == 0:
        return {
            'mean_abs_corr': 0.0,
            'edge_density': 0.0,
            'max_abs_corr': 0.0,
            'avg_clustering_coeff': 0.0
        }
    
    edges = [abs(graph[u][v]['weight']) for u, v in graph.edges()]
    n_nodes = graph.number_of_nodes()
    n_edges = graph.number_of_edges()
    max_possible_edges = n_nodes * (n_nodes - 1) / 2
    
    mean_abs_corr = np.mean(edges)
    edge_density = n_edges / max_possible_edges if max_possible_edges > 0 else 0.0
    max_abs_corr = np.max(edges)
    avg_clustering_coeff = nx.average_clustering(graph)
    
    return {
        'mean_abs_corr': mean_abs_corr,
        'edge_density': edge_density,
        'max_abs_corr': max_abs_corr,
        'avg_clustering_coeff': avg_clustering_coeff
    }

def generate_null_distribution(
    df: pd.DataFrame, 
    n_permutations: int, 
    stats_func: Callable[[pd.DataFrame], dict],
    variable_count: int = None
) -> dict:
    """
    Generate null distribution via permutation.
    
    Implements performance optimization (T031):
    If calculating clustering coefficient and variable_count > 50,
    reduce n_permutations to 500 to ensure runtime < 6h.
    """
    stats_keys = stats_func(df).keys()
    null_dists = {k: [] for k in stats_keys}
    
    # T031 Optimization: Reduce N for clustering coefficient on large datasets
    effective_n_permutations = n_permutations
    if variable_count is not None and variable_count > 50:
        # Check if clustering coefficient is being calculated
        if 'avg_clustering_coeff' in stats_keys:
            effective_n_permutations = 500
    
    for _ in range(effective_n_permutations):
        permuted_df = df.apply(np.random.permutation)
        perm_stats = stats_func(permuted_df)
        for k, v in perm_stats.items():
            null_dists[k].append(v)
    
    return null_dists

def generate_synthetic_dataset(n_samples: int = 500, n_vars: int = 20) -> pd.DataFrame:
    """Generate synthetic dataset with identity covariance (no correlation)."""
    data = np.random.randn(n_samples, n_vars)
    columns = [f"var_{i}" for i in range(n_vars)]
    return pd.DataFrame(data, columns=columns)

def validate_null_model(
    synthetic_df: pd.DataFrame,
    n_permutations: int = 1000,
    threshold: float = 0.3
) -> Dict[str, float]:
    """Validate null model using synthetic data."""
    def stats_func(df):
        corr = compute_correlation(df, 'pearson')
        graph = construct_graph(corr, threshold)
        return calculate_stats(graph)
    
    null_dist = generate_null_distribution(synthetic_df, n_permutations, stats_func)
    
    # Calculate p-values for observed stats (which should be ~0 for synthetic)
    observed_stats = stats_func(synthetic_df)
    p_values = {}
    for k in null_dist.keys():
        observed_val = observed_stats[k]
        null_vals = null_dist[k]
        # Two-tailed p-value
        count_extreme = sum(1 for v in null_vals if abs(v) >= abs(observed_val))
        p_values[k] = (count_extreme + 1) / (n_permutations + 1)
    
    return p_values

def compute_correlation_matrix_with_stats(
    df: pd.DataFrame,
    method: str = 'pearson',
    threshold: float = 0.3
) -> Tuple[pd.DataFrame, nx.Graph, dict]:
    """Compute correlation, construct graph, and calculate stats."""
    corr_matrix = compute_correlation(df, method)
    graph = construct_graph(corr_matrix, threshold)
    stats_dict = calculate_stats(graph, df)
    return corr_matrix, graph, stats_dict

def calculate_empirical_p_value(
    observed_val: float,
    null_dist: List[float]
) -> float:
    """Calculate empirical p-value from null distribution."""
    n = len(null_dist)
    count = sum(1 for v in null_dist if abs(v) >= abs(observed_val))
    return (count + 1) / (n + 1)

def save_exploratory_spearman_matrices(
    df: pd.DataFrame,
    output_dir: str,
    dataset_id: str
) -> None:
    """Save Spearman correlation matrices for exploratory analysis."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    spearman_corr = compute_correlation(df, 'spearman')
    output_path = os.path.join(output_dir, f"{dataset_id}_spearman.csv")
    spearman_corr.to_csv(output_path)

def apply_benjamini_yekutieli_correction(
    p_values: List[float],
    alpha: float = 0.05
) -> Tuple[List[float], List[bool]]:
    """Apply Benjamini-Yekutieli correction to p-values."""
    from correction import benjamini_yekutieli
    return benjamini_yekutieli(p_values, alpha)

def run_full_analysis_pipeline(
    df: pd.DataFrame,
    dataset_id: str,
    n_permutations: int = 1000,
    threshold: float = 0.3,
    output_dir: str = "output/results"
) -> Dict[str, Any]:
    """Run full analysis pipeline on a dataset."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    # Compute observed stats
    corr_matrix, graph, observed_stats = compute_correlation_matrix_with_stats(
        df, 'pearson', threshold
    )
    
    # Generate null distribution
    n_vars = df.shape[1]
    null_dist = generate_null_distribution(
        df, n_permutations, 
        lambda d: calculate_stats(construct_graph(compute_correlation(d, 'pearson'), threshold)),
        variable_count=n_vars
    )
    
    # Calculate p-values
    p_values = {}
    q_values = {}
    is_significant = {}
    for stat_name in observed_stats.keys():
        obs_val = observed_stats[stat_name]
        null_vals = null_dist[stat_name]
        p_val = calculate_empirical_p_value(obs_val, null_vals)
        p_values[stat_name] = p_val
    
    # Apply BY correction
    all_p_values = list(p_values.values())
    corrected = apply_benjamini_yekutieli_correction(all_p_values)
    q_values_list, sig_flags = corrected
    
    for i, stat_name in enumerate(p_values.keys()):
        q_values[stat_name] = q_values_list[i]
        is_significant[stat_name] = sig_flags[i]
    
    # Save results
    results = {
        'dataset_id': dataset_id,
        'observed': observed_stats,
        'p_values': p_values,
        'q_values': q_values,
        'is_significant': is_significant,
        'threshold': threshold,
        'n_permutations': n_permutations,
        'n_variables': n_vars
    }
    
    output_path = os.path.join(output_dir, f"{dataset_id}_results.json")
    import json
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    return results