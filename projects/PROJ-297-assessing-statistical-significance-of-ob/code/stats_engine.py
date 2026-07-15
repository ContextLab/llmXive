import pandas as pd
import numpy as np
from scipy import stats
import networkx as nx
from typing import Callable, Dict, List, Optional, Tuple, Any
import config

def compute_correlation(df: pd.DataFrame, method: str = 'pearson') -> pd.DataFrame:
    """
    Compute correlation matrix for the given DataFrame.
    
    Args:
        df: Input DataFrame with numeric columns
        method: 'pearson' or 'spearman'
        
    Returns:
        Correlation matrix as DataFrame
    """
    if method == 'pearson':
        return df.corr(method='pearson')
    elif method == 'spearman':
        return df.corr(method='spearman')
    else:
        raise ValueError(f"Unknown correlation method: {method}")

def construct_graph(corr_matrix: pd.DataFrame, threshold: float) -> nx.Graph:
    """
    Construct a graph from correlation matrix with absolute threshold.
    
    Args:
        corr_matrix: Correlation matrix (absolute values)
        threshold: Threshold for edge inclusion
        
    Returns:
        NetworkX graph with edges where |correlation| > threshold
    """
    G = nx.Graph()
    
    # Add nodes
    G.add_nodes_from(corr_matrix.columns)
    
    # Add edges where |correlation| > threshold
    for i, var1 in enumerate(corr_matrix.columns):
        for j, var2 in enumerate(corr_matrix.columns):
            if i < j:  # Avoid duplicates and self-loops
                if abs(corr_matrix.loc[var1, var2]) > threshold:
                    G.add_edge(var1, var2, weight=abs(corr_matrix.loc[var1, var2]))
    
    return G

def calculate_stats(graph: nx.Graph) -> Dict[str, float]:
    """
    Calculate network statistics from a graph.
    
    Args:
        graph: NetworkX graph
        
    Returns:
        Dictionary with network statistics
    """
    if graph.number_of_edges() == 0:
        return {
            'mean_abs_correlation': 0.0,
            'edge_density': 0.0,
            'max_abs_correlation': 0.0,
            'average_clustering_coefficient': 0.0
        }
    
    # Mean absolute correlation (average edge weight)
    mean_abs_corr = np.mean([data['weight'] for _, _, data in graph.edges(data=True)])
    
    # Edge density
    edge_density = nx.density(graph)
    
    # Max absolute correlation
    max_abs_corr = max([data['weight'] for _, _, data in graph.edges(data=True)])
    
    # Average clustering coefficient
    avg_clustering = nx.average_clustering(graph)
    
    return {
        'mean_abs_correlation': mean_abs_corr,
        'edge_density': edge_density,
        'max_abs_correlation': max_abs_corr,
        'average_clustering_coefficient': avg_clustering
    }

def generate_null_distribution(df: pd.DataFrame, n_permutations: int, stats_func: Callable) -> Dict[str, List[float]]:
    """
    Generate null distribution by permuting data and computing statistics.
    
    Args:
        df: Original DataFrame
        n_permutations: Number of permutations
        stats_func: Function to compute statistics from a DataFrame
        
    Returns:
        Dictionary mapping statistic names to lists of null values
    """
    null_distributions = {}
    columns = df.columns
    n_cols = len(columns)
    
    # Initialize null distributions
    for stat_name in ['mean_abs_correlation', 'edge_density', 'max_abs_correlation', 'average_clustering_coefficient']:
        null_distributions[stat_name] = []
    
    # Pre-compute threshold for graph construction
    # Note: The threshold is embedded in the stats_func closure
    
    for i in range(n_permutations):
        # Permute each column independently to preserve marginals
        permuted_df = df.copy()
        for col in columns:
            permuted_df[col] = np.random.permutation(permuted_df[col].values)
        
        # Compute statistics for permuted data
        perm_stats = stats_func(permuted_df)
        
        # Store null values
        for stat_name, stat_val in perm_stats.items():
            null_distributions[stat_name].append(stat_val)
    
    return null_distributions

def generate_synthetic_dataset(n_samples: int = 500, n_vars: int = 20, random_seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic dataset with identity covariance (no correlations).
    
    Args:
        n_samples: Number of samples
        n_vars: Number of variables
        random_seed: Random seed for reproducibility
        
    Returns:
        DataFrame with synthetic data
    """
    np.random.seed(random_seed)
    data = np.random.randn(n_samples, n_vars)
    columns = [f'var_{i}' for i in range(n_vars)]
    return pd.DataFrame(data, columns=columns)

def validate_null_model(n_runs: int = 100) -> Dict[str, Any]:
    """
    Validate null model by running synthetic data through the pipeline.
    
    Args:
        n_runs: Number of validation runs
        
    Returns:
        Dictionary with validation results
    """
    pass_rate = 0
    results = []
    
    for i in range(n_runs):
        # Generate synthetic data with no correlations
        df = generate_synthetic_dataset()
        
        # Compute observed statistics
        corr_matrix = compute_correlation(df, method='pearson')
        graph = construct_graph(corr_matrix, config.DEFAULT_THRESHOLD)
        observed_stats = calculate_stats(graph)
        
        # Generate null distribution
        null_dist = generate_null_distribution(
            df, config.DEFAULT_N_PERMUTATIONS,
            lambda d: calculate_stats(construct_graph(compute_correlation(d, method='pearson'), config.DEFAULT_THRESHOLD))
        )
        
        # Calculate p-values
        p_values = {}
        for stat_name, stat_val in observed_stats.items():
            p_values[stat_name] = calculate_empirical_p_value(null_dist[stat_name], stat_val)
        
        # Check if p > 0.05 for all statistics (null model should not reject)
        all_non_significant = all(p > 0.05 for p in p_values.values())
        if all_non_significant:
            pass_rate += 1
        
        results.append({
            'run': i,
            'p_values': p_values,
            'passed': all_non_significant
        })
    
    return {
        'pass_rate': pass_rate / n_runs,
        'n_runs': n_runs,
        'results': results
    }

def compute_correlation_matrix_with_stats(df: pd.DataFrame, method: str = 'pearson') -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Compute correlation matrix and additional statistics.
    
    Args:
        df: Input DataFrame
        method: Correlation method
        
    Returns:
        Tuple of (correlation matrix, statistics dictionary)
    """
    corr_matrix = compute_correlation(df, method)
    
    # Additional statistics
    stats_dict = {
        'mean_correlation': corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)].mean(),
        'max_correlation': corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)].max(),
        'min_correlation': corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)].min()
    }
    
    return corr_matrix, stats_dict

def calculate_empirical_p_value(null_dist: List[float], observed_val: float) -> float:
    """
    Calculate empirical p-value from null distribution.
    
    Args:
        null_dist: List of null values
        observed_val: Observed statistic value
        
    Returns:
        Empirical p-value using (r+1)/(N+1) formula
    """
    n = len(null_dist)
    r = sum(1 for val in null_dist if val >= observed_val)
    return (r + 1) / (n + 1)

def save_exploratory_spearman_matrices(df: pd.DataFrame, output_dir: str) -> None:
    """
    Save Spearman correlation matrices to exploratory directory.
    
    Args:
        df: Input DataFrame
        output_dir: Output directory path
    """
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    spearman_corr = compute_correlation(df, method='spearman')
    output_path = os.path.join(output_dir, f"spearman_{df.columns[0]}_matrix.csv")
    spearman_corr.to_csv(output_path)
    print(f"Spearman matrix saved to {output_path}")

def apply_benjamini_yekutieli_correction(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Yekutieli correction to p-values.
    
    Args:
        p_values: List of p-values
        
    Returns:
        List of corrected q-values
    """
    from correction import benjamini_yekutieli
    return benjamini_yekutieli(p_values)

def run_full_analysis_pipeline(df: pd.DataFrame, threshold: float, n_permutations: int) -> Dict[str, Any]:
    """
    Run the full analysis pipeline on a dataset.
    
    Args:
        df: Input DataFrame
        threshold: Correlation threshold
        n_permutations: Number of permutations
        
    Returns:
        Dictionary with analysis results
    """
    # Compute correlation matrix
    corr_matrix = compute_correlation(df, method='pearson')
    
    # Construct graph
    graph = construct_graph(corr_matrix, threshold)
    
    # Calculate observed statistics
    observed_stats = calculate_stats(graph)
    
    # Generate null distribution
    null_dist = generate_null_distribution(
        df, n_permutations,
        lambda d: calculate_stats(construct_graph(compute_correlation(d, method='pearson'), threshold))
    )
    
    # Calculate p-values
    p_values = {}
    for stat_name, stat_val in observed_stats.items():
        p_values[stat_name] = calculate_empirical_p_value(null_dist[stat_name], stat_val)
    
    return {
        'statistics': observed_stats,
        'p_values': p_values,
        'null_distributions': null_dist,
        'graph': graph,
        'correlation_matrix': corr_matrix
    }
