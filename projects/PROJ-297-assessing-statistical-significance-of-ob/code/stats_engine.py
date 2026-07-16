import pandas as pd
import numpy as np
from scipy import stats
import networkx as nx
from typing import Callable, Dict, List, Optional, Tuple, Any
import config
import os
import json
import gc

def get_config():
    return config.get_config()

def compute_correlation(df: pd.DataFrame, method: str = 'pearson') -> pd.DataFrame:
    """Compute correlation matrix for numeric columns."""
    if method == 'pearson':
        corr_matrix = df.corr(method='pearson')
    elif method == 'spearman':
        corr_matrix = df.corr(method='spearman')
    else:
        raise ValueError(f"Unsupported method: {method}")
    return corr_matrix

def construct_graph(corr_matrix: pd.DataFrame, threshold: float) -> nx.Graph:
    """Construct a graph from correlation matrix with given threshold."""
    G = nx.Graph()
    nodes = corr_matrix.columns
    G.add_nodes_from(nodes)
    
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            node_i, node_j = nodes[i], nodes[j]
            corr_val = corr_matrix.loc[node_i, node_j]
            if abs(corr_val) > threshold:
                G.add_edge(node_i, node_j, weight=corr_val)
    return G

def calculate_stats(graph: nx.Graph) -> Dict[str, float]:
    """Calculate network statistics."""
    if graph.number_of_edges() == 0:
        return {
            "mean_abs_corr": 0.0,
            "edge_density": 0.0,
            "max_abs_corr": 0.0,
            "avg_clustering": 0.0
        }
    
    abs_corrs = [abs(d['weight']) for u, v, d in graph.edges(data=True)]
    n = graph.number_of_nodes()
    m = graph.number_of_edges()
    
    return {
        "mean_abs_corr": np.mean(abs_corrs),
        "edge_density": m / (n * (n - 1) / 2) if n > 1 else 0.0,
        "max_abs_corr": np.max(abs_corrs),
        "avg_clustering": nx.average_clustering(graph)
    }

def generate_null_distribution(df: pd.DataFrame, n_permutations: int, stats_func: Callable) -> Dict[str, Any]:
    """
    Generate null distribution via permutation.
    Implements chunked processing for memory efficiency.
    """
    rng = np.random.default_rng(seed=get_config()['random_seed'])
    observed_stats = stats_func(df)
    null_stats = {k: [] for k in observed_stats.keys()}
    
    n_rows = df.shape[0]
    n_cols = df.shape[1]
    
    # Pre-allocate memory for permutation if possible, but stream results
    # to avoid holding all permutations in memory at once.
    
    for i in range(n_permutations):
        # Permute rows independently for each column to break correlation
        # while preserving marginals
        permuted_df = df.apply(lambda col: rng.permutation(col.values))
        
        # Compute stats on permuted data
        perm_stats = stats_func(permuted_df)
        
        for k in null_stats.keys():
            null_stats[k].append(perm_stats[k])
        
        # Force garbage collection periodically to prevent OOM
        if (i + 1) % 500 == 0:
            gc.collect()
    
    return {
        "observed": observed_stats,
        "null": null_stats
    }

def generate_synthetic_dataset(n_samples: int = 500, n_vars: int = 20) -> pd.DataFrame:
    """Generate synthetic dataset with identity covariance (no correlation)."""
    rng = np.random.default_rng(seed=get_config()['random_seed'])
    data = rng.standard_normal((n_samples, n_vars))
    columns = [f"V{i}" for i in range(n_vars)]
    return pd.DataFrame(data, columns=columns)

def validate_null_model(n_runs: int = 100) -> Dict[str, Any]:
    """Validate null model by running synthetic data 100 times."""
    results = []
    for _ in range(n_runs):
        df = generate_synthetic_dataset()
        # Compute observed correlation
        corr_matrix = compute_correlation(df, method='pearson')
        
        # Define a simple stats function for validation
        def simple_stats_func(data):
            c = data.corr()
            return {
                "mean_abs_corr": np.mean(np.abs(c.values[np.triu_indices_from(c, k=1)])),
                "edge_density": 0.0, # Simplified for validation
                "max_abs_corr": np.max(np.abs(c.values)),
                "avg_clustering": 0.0
            }
        
        null_dist = generate_null_distribution(df, n_permutations=2000, stats_func=simple_stats_func)
        
        # Calculate p-value
        obs_val = null_dist["observed"]["mean_abs_corr"]
        null_vals = null_dist["null"]["mean_abs_corr"]
        p_val = (sum(v >= obs_val for v in null_vals) + 1) / (len(null_vals) + 1)
        
        results.append(p_val > 0.05)
    
    success_rate = sum(results) / n_runs
    return {
        "success_rate": success_rate,
        "passed_runs": sum(results),
        "total_runs": n_runs
    }

def compute_correlation_matrix_with_stats(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Compute both Pearson and Spearman matrices."""
    return {
        "pearson": compute_correlation(df, method='pearson'),
        "spearman": compute_correlation(df, method='spearman')
    }

def calculate_empirical_p_value(observed: float, null_distribution: List[float]) -> float:
    """Calculate empirical p-value using (r+1)/(N+1)."""
    r = sum(1 for x in null_distribution if x >= observed)
    return (r + 1) / (len(null_distribution) + 1)

def save_exploratory_spearman_matrices(results: Dict[str, Any], output_dir: str):
    """Save Spearman matrices to exploratory directory."""
    os.makedirs(output_dir, exist_ok=True)
    for dataset_id, data in results.items():
        if "spearman" in data:
            path = os.path.join(output_dir, f"{dataset_id}_spearman.csv")
            data["spearman"].to_csv(path)

def apply_benjamini_yekutieli_correction(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """Apply BY correction to list of p-values."""
    from correction import benjamini_yekutieli
    return benjamini_yekutieli(np.array(p_values), alpha)

def run_full_analysis_pipeline(datasets: List[str], n_permutations: int = 2000, threshold: float = 0.3) -> Dict[str, Any]:
    """Run the full analysis pipeline on a list of datasets."""
    from loaders import load_and_hygiene_dataset
    from correction import apply_correction_to_results
    
    results = {}
    
    for ds_name in datasets:
        print(f"Processing dataset: {ds_name}")
        try:
            df = load_and_hygiene_dataset(ds_name)
            
            # Compute correlation
            corr_data = compute_correlation_matrix_with_stats(df)
            pearson_corr = corr_data["pearson"]
            
            # Construct graph
            G = construct_graph(pearson_corr, threshold)
            
            # Calculate stats
            observed_stats = calculate_stats(G)
            
            # Define stats function for permutation
            def graph_stats_func(data):
                c = data.corr()
                g = construct_graph(c, threshold)
                return calculate_stats(g)
            
            # Generate null distribution
            null_dist = generate_null_distribution(df, n_permutations, graph_stats_func)
            
            # Calculate p-values
            p_values = {}
            for k in observed_stats.keys():
                p_values[k] = calculate_empirical_p_value(observed_stats[k], null_dist["null"][k])
            
            # Apply BY correction
            p_list = list(p_values.values())
            q_values = apply_benjamini_yekutieli_correction(p_list)
            q_dict = {k: q for k, q in zip(p_values.keys(), q_values)}
            
            # Determine significance
            is_sig = {k: q < 0.05 for k, q in q_dict.items()}
            
            results[ds_name] = {
                "observed": observed_stats,
                "p_values": p_values,
                "q_values": q_dict,
                "is_significant": is_sig,
                "spearman": corr_data["spearman"]
            }
            
        except Exception as e:
            print(f"Error processing {ds_name}: {e}")
            continue
    
    return results
