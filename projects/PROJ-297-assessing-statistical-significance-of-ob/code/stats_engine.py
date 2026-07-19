import pandas as pd
import numpy as np
from scipy import stats
import networkx as nx
from typing import Callable, Dict, List, Optional, Tuple, Any
import config
import logging
import os
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import time

# Configure logging for stats_engine
logger = logging.getLogger(__name__)

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
        corr_matrix, _ = stats.pearsonr(df.T, df.T)
        # Handle case where pearsonr might return scalar for single column
        if np.isscalar(corr_matrix):
            return pd.DataFrame(np.array([[1.0]]), index=df.columns, columns=df.columns)
        return pd.DataFrame(corr_matrix, index=df.columns, columns=df.columns)
    elif method == 'spearman':
        corr_matrix, _ = stats.spearmanr(df.T, df.T)
        if np.isscalar(corr_matrix):
            return pd.DataFrame(np.array([[1.0]]), index=df.columns, columns=df.columns)
        return pd.DataFrame(corr_matrix, index=df.columns, columns=df.columns)
    else:
        raise ValueError(f"Unsupported correlation method: {method}")

def construct_graph(corr_matrix: pd.DataFrame, threshold: float = 0.3) -> nx.Graph:
    """
    Construct a network graph from correlation matrix.
    
    Args:
        corr_matrix: Correlation matrix DataFrame
        threshold: Absolute correlation threshold for edge inclusion
    
    Returns:
        NetworkX graph
    """
    G = nx.Graph()
    variables = corr_matrix.columns.tolist()
    
    # Add nodes
    for var in variables:
        G.add_node(var)
    
    # Add edges based on threshold
    for i in range(len(variables)):
        for j in range(i + 1, len(variables)):
            var_i = variables[i]
            var_j = variables[j]
            corr_val = corr_matrix.loc[var_i, var_j]
            
            if abs(corr_val) > threshold:
                G.add_edge(var_i, var_j, weight=corr_val)
    
    return G

def calculate_stats(graph: nx.Graph) -> Dict[str, float]:
    """
    Calculate network statistics from a graph.
    
    Args:
        graph: NetworkX graph
    
    Returns:
        Dictionary of network statistics
    """
    stats_dict = {}
    
    if graph.number_of_edges() == 0:
        stats_dict['mean_absolute_correlation'] = 0.0
        stats_dict['edge_density'] = 0.0
        stats_dict['max_absolute_correlation'] = 0.0
        stats_dict['average_clustering_coefficient'] = 0.0
        return stats_dict
    
    # Mean Absolute Correlation
    abs_corrs = [abs(graph[u][v]['weight']) for u, v in graph.edges()]
    stats_dict['mean_absolute_correlation'] = np.mean(abs_corrs)
    
    # Edge Density
    n_nodes = graph.number_of_nodes()
    n_edges = graph.number_of_edges()
    max_edges = n_nodes * (n_nodes - 1) / 2
    stats_dict['edge_density'] = n_edges / max_edges if max_edges > 0 else 0.0
    
    # Max Absolute Correlation
    stats_dict['max_absolute_correlation'] = np.max(abs_corrs)
    
    # Average Clustering Coefficient
    # Handle disconnected graphs by checking if graph is connected
    if nx.is_connected(graph):
        stats_dict['average_clustering_coefficient'] = nx.average_clustering(graph)
    else:
        # Calculate on largest connected component
        largest_cc = max(nx.connected_components(graph), key=len)
        subgraph = graph.subgraph(largest_cc)
        stats_dict['average_clustering_coefficient'] = nx.average_clustering(subgraph)
    
    return stats_dict

def generate_null_distribution(
    df: pd.DataFrame, 
    n_permutations: int, 
    threshold: float = 0.3,
    stats_func: Optional[Callable] = None,
    seed: Optional[int] = None,
    n_workers: int = 1
) -> Dict[str, Any]:
    """
    Generate null distribution via permutation testing.
    
    Args:
        df: Input DataFrame
        n_permutations: Number of permutations
        threshold: Correlation threshold for graph construction
        stats_func: Function to calculate statistics (default: calculate_stats)
        seed: Random seed for reproducibility
        n_workers: Number of parallel workers
    
    Returns:
        Dictionary containing null distribution results
    """
    if stats_func is None:
        stats_func = calculate_stats
    
    if seed is not None:
        np.random.seed(seed)
    
    # Define worker function for parallel execution
    def permute_worker(args):
        perm_idx, local_seed = args
        np.random.seed(local_seed)
        
        # Permute columns
        perm_df = df.copy()
        for col in perm_df.columns:
            perm_df[col] = perm_df[col].sample(frac=1, random_state=local_seed + perm_idx).reset_index(drop=True)
        
        # Compute correlation and graph
        corr_matrix = compute_correlation(perm_df, method='pearson')
        graph = construct_graph(corr_matrix, threshold=threshold)
        graph_stats = stats_func(graph)
        
        return graph_stats
    
    # Prepare arguments for parallel execution
    worker_args = [(i, seed + i) if seed else (i, np.random.randint(0, 2**31)) for i in range(n_permutations)]
    
    # Execute permutations
    null_stats = {
        'mean_absolute_correlation': [],
        'edge_density': [],
        'max_absolute_correlation': [],
        'average_clustering_coefficient': []
    }
    
    if n_workers > 1 and n_permutations > 1:
        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            futures = [executor.submit(permute_worker, arg) for arg in worker_args]
            for future in as_completed(futures):
                result = future.result()
                for key in null_stats:
                    null_stats[key].append(result[key])
    else:
        for arg in worker_args:
            result = permute_worker(arg)
            for key in null_stats:
                null_stats[key].append(result[key])
    
    # Convert to numpy arrays
    for key in null_stats:
        null_stats[key] = np.array(null_stats[key])
    
    return null_stats

def calculate_empirical_p_value(
    observed_value: float, 
    null_distribution: np.ndarray,
    n_permutations: int
) -> float:
    """
    Calculate empirical p-value with floor enforcement.
    
    Args:
        observed_value: Observed statistic value
        null_distribution: Array of null distribution values
        n_permutations: Number of permutations used (N)
    
    Returns:
        Empirical p-value with floor of 1/(N+1)
    
    Note:
        Implements T078: P-Value Floor Enforcement
        Formula: (r+1)/(N+1) where r is count of null values >= observed
        This ensures p >= 1/(N+1), preventing p=0
    """
    # Count how many null values are >= observed (for right-tailed test)
    # For two-tailed or different tests, adjust comparison as needed
    r = np.sum(null_distribution >= observed_value)
    
    # T078: Enforce minimum p-value floor
    # Formula: (r+1)/(N+1)
    p_value = (r + 1) / (n_permutations + 1)
    
    # Explicit floor enforcement (redundant but explicit per T078)
    min_p = 1.0 / (n_permutations + 1)
    p_value = max(p_value, min_p)
    
    return p_value

def generate_synthetic_dataset(n_samples: int = 500, n_vars: int = 20, seed: Optional[int] = None) -> pd.DataFrame:
    """
    Generate synthetic dataset with identity covariance (no correlations).
    
    Args:
        n_samples: Number of samples
        n_vars: Number of variables
        seed: Random seed
    
    Returns:
        DataFrame with synthetic data
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Identity covariance matrix
    cov = np.eye(n_vars)
    mean = np.zeros(n_vars)
    
    # Generate multivariate normal data
    data = np.random.multivariate_normal(mean, cov, size=n_samples)
    
    # Create DataFrame
    columns = [f'var_{i}' for i in range(n_vars)]
    df = pd.DataFrame(data, columns=columns)
    
    # Variance check (T076)
    for col in df.columns:
        if df[col].var() == 0:
            raise ValueError(f"Synthetic data generation failed: Variable {col} has zero variance")
    
    return df

def validate_null_model(
    df: pd.DataFrame,
    n_permutations: int = 2000,
    threshold: float = 0.3,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Validate that observed statistics fall within null distribution.
    
    Args:
        df: Input DataFrame (should be identity covariance for validation)
        n_permutations: Number of permutations
        threshold: Correlation threshold
        seed: Random seed
    
    Returns:
        Dictionary with validation results
    """
    # Compute observed statistics
    corr_matrix = compute_correlation(df, method='pearson')
    graph = construct_graph(corr_matrix, threshold=threshold)
    observed_stats = calculate_stats(graph)
    
    # Generate null distribution
    null_dist = generate_null_distribution(df, n_permutations, threshold, seed=seed)
    
    # Calculate p-values
    p_values = {}
    for key in observed_stats:
        p_values[key] = calculate_empirical_p_value(
            observed_stats[key], 
            null_dist[key], 
            n_permutations
        )
    
    # Check if p > 0.05 (should be true for identity covariance)
    validation_passed = all(p > 0.05 for p in p_values.values())
    
    return {
        'observed_stats': observed_stats,
        'p_values': p_values,
        'validation_passed': validation_passed
    }

def compute_correlation_matrix_with_stats(
    df: pd.DataFrame,
    method: str = 'pearson',
    threshold: float = 0.3,
    n_permutations: int = 2000,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Complete analysis pipeline for a single dataset.
    
    Args:
        df: Input DataFrame
        method: Correlation method
        threshold: Correlation threshold
        n_permutations: Number of permutations
        seed: Random seed
    
    Returns:
        Dictionary with all analysis results
    """
    # Compute correlation matrix
    corr_matrix = compute_correlation(df, method=method)
    
    # Construct graph
    graph = construct_graph(corr_matrix, threshold=threshold)
    
    # Calculate observed statistics
    observed_stats = calculate_stats(graph)
    
    # Generate null distribution
    null_dist = generate_null_distribution(
        df, 
        n_permutations, 
        threshold,
        seed=seed,
        n_workers=multiprocessing.cpu_count()
    )
    
    # Calculate empirical p-values
    p_values = {}
    for key in observed_stats:
        p_values[key] = calculate_empirical_p_value(
            observed_stats[key],
            null_dist[key],
            n_permutations
        )
    
    return {
        'correlation_matrix': corr_matrix,
        'graph': graph,
        'observed_stats': observed_stats,
        'null_distribution': null_dist,
        'p_values': p_values,
        'n_permutations': n_permutations
    }

def save_exploratory_spearman_matrices(
    df: pd.DataFrame,
    output_dir: str = 'output/exploratory'
) -> None:
    """
    Save Spearman correlation matrices for exploratory analysis only.
    
    Args:
        df: Input DataFrame
        output_dir: Output directory path
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Compute Spearman correlation
    spearman_corr = compute_correlation(df, method='spearman')
    
    # Save to CSV
    output_path = os.path.join(output_dir, 'spearman_correlation_matrix.csv')
    spearman_corr.to_csv(output_path)
    
    logger.info(f"Spearman correlation matrix saved to {output_path}")

def apply_benjamini_yekutieli_correction(
    p_values: List[float],
    alpha: float = 0.05
) -> Tuple[List[float], List[bool]]:
    """
    Apply Benjamini-Yekutieli correction to p-values.
    
    Args:
        p_values: List of raw p-values
        alpha: Significance level
    
    Returns:
        Tuple of (q_values, significance_flags)
    """
    from correction import benjamini_yekutieli
    return benjamini_yekutieli(p_values, alpha)

def run_full_analysis_pipeline(
    datasets: List[Tuple[str, pd.DataFrame]],
    n_permutations: int = 2000,
    threshold: float = 0.3,
    alpha: float = 0.05,
    seed: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Run full analysis pipeline on multiple datasets.
    
    Args:
        datasets: List of (dataset_id, DataFrame) tuples
        n_permutations: Number of permutations per dataset
        threshold: Correlation threshold
        alpha: Significance level for correction
        seed: Random seed
    
    Returns:
        List of analysis results for each dataset
    """
    results = []
    
    for dataset_id, df in datasets:
        logger.info(f"Processing dataset: {dataset_id}")
        
        # Compute correlation and statistics
        analysis_result = compute_correlation_matrix_with_stats(
            df,
            method='pearson',
            threshold=threshold,
            n_permutations=n_permutations,
            seed=seed
        )
        
        # Apply BY correction
        p_values = list(analysis_result['p_values'].values())
        q_values, is_significant = apply_benjamini_yekutieli_correction(p_values, alpha)
        
        # Store results
        result_entry = {
            'dataset_id': dataset_id,
            'n_permutations': n_permutations,
            'threshold': threshold,
            'observed_stats': analysis_result['observed_stats'],
            'p_values': dict(zip(analysis_result['observed_stats'].keys(), p_values)),
            'q_values': dict(zip(analysis_result['observed_stats'].keys(), q_values)),
            'is_significant': dict(zip(analysis_result['observed_stats'].keys(), is_significant))
        }
        
        results.append(result_entry)
    
    return results

def main():
    """
    Main function for standalone execution.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Stats Engine for Correlation Analysis')
    parser.add_argument('--dataset', type=str, help='Path to dataset CSV')
    parser.add_argument('--n_permutations', type=int, default=2000, help='Number of permutations')
    parser.add_argument('--threshold', type=float, default=0.3, help='Correlation threshold')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--output', type=str, default='output/results', help='Output directory')
    
    args = parser.parse_args()
    
    if args.dataset:
        # Load dataset
        df = pd.read_csv(args.dataset)
        
        # Run analysis
        result = compute_correlation_matrix_with_stats(
            df,
            n_permutations=args.n_permutations,
            threshold=args.threshold,
            seed=args.seed
        )
        
        # Save results
        os.makedirs(args.output, exist_ok=True)
        output_path = os.path.join(args.output, 'analysis_results.json')
        import json
        # Convert numpy types to Python types for JSON serialization
        serializable_result = {}
        for key, value in result.items():
            if isinstance(value, dict):
                serializable_result[key] = {k: float(v) if isinstance(v, (np.floating, np.integer)) else v for k, v in value.items()}
            elif isinstance(value, np.ndarray):
                serializable_result[key] = value.tolist()
            else:
                serializable_result[key] = value
        
        with open(output_path, 'w') as f:
            json.dump(serializable_result, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")

if __name__ == '__main__':
    main()