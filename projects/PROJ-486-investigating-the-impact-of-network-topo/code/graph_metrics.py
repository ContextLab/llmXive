import numpy as np
import pandas as pd
import networkx as nx
from typing import Union, Dict, List, Optional
import json
import os

def calculate_clustering_coefficient(correlation_matrix: Union[np.ndarray, pd.DataFrame]) -> float:
    """
    Calculate the weighted clustering coefficient for a correlation matrix.
    
    Args:
        correlation_matrix: N x N correlation matrix (numpy array or DataFrame)
        
    Returns:
        float: Average clustering coefficient across all nodes
    """
    if isinstance(correlation_matrix, pd.DataFrame):
        correlation_matrix = correlation_matrix.values
        
    # Convert to networkx graph
    G = nx.from_numpy_array(correlation_matrix)
    
    # Calculate weighted clustering coefficient
    clustering_coeffs = nx.clustering(G, weight='weight')
    
    return float(np.mean(list(clustering_coeffs.values())))

def calculate_path_length(correlation_matrix: Union[np.ndarray, pd.DataFrame]) -> float:
    """
    Calculate the characteristic path length for a correlation matrix.
    
    Args:
        correlation_matrix: N x N correlation matrix (numpy array or DataFrame)
        
    Returns:
        float: Characteristic path length
    """
    if isinstance(correlation_matrix, pd.DataFrame):
        correlation_matrix = correlation_matrix.values
        
    # Convert to networkx graph
    G = nx.from_numpy_array(correlation_matrix)
    
    # Calculate characteristic path length
    try:
        path_length = nx.average_shortest_path_length(G, weight='weight')
    except nx.NetworkXError:
        # If graph is disconnected, use infinity or a large number
        path_length = float('inf')
        
    return float(path_length)

def compute_all_metrics(correlation_matrix: Union[np.ndarray, pd.DataFrame]) -> Dict[str, float]:
    """
    Compute all network topology metrics for a given correlation matrix.
    
    Args:
        correlation_matrix: N x N correlation matrix (numpy array or DataFrame)
        
    Returns:
        Dict containing clustering coefficient and path length
    """
    return {
        'clustering_coefficient': calculate_clustering_coefficient(correlation_matrix),
        'path_length': calculate_path_length(correlation_matrix)
    }

def process_subject_matrices(matrices_df: pd.DataFrame) -> pd.DataFrame:
    """
    Process a DataFrame of correlation matrices and compute metrics for each subject.
    
    Args:
        matrices_df: DataFrame with subject_id and correlation matrix columns
        
    Returns:
        DataFrame with subject_id and computed metrics
    """
    results = []
    
    for _, row in matrices_df.iterrows():
        subject_id = row['subject_id']
        # Assuming matrix data is stored in columns starting with 'node_'
        matrix_cols = [col for col in row.index if col.startswith('node_')]
        
        if len(matrix_cols) == 0:
            continue
            
        # Reconstruct matrix (assuming square matrix stored as rows)
        matrix_size = int(np.sqrt(len(matrix_cols)))
        if matrix_size * matrix_size != len(matrix_cols):
            continue
            
        matrix_data = row[matrix_cols].values
        correlation_matrix = matrix_data.reshape(matrix_size, matrix_size)
        
        metrics = compute_all_metrics(correlation_matrix)
        metrics['subject_id'] = subject_id
        results.append(metrics)
        
    return pd.DataFrame(results)

def detect_zero_variance_metrics(metrics_df: pd.DataFrame, threshold: float = 1e-9) -> List[str]:
    """
    Detect metrics with zero variance (std < threshold).
    
    Args:
        metrics_df: DataFrame with metric columns
        threshold: Variance threshold below which a metric is considered zero-variance
        
    Returns:
        List of metric names that have zero variance
    """
    zero_var_metrics = []
    
    for col in metrics_df.columns:
        if col == 'subject_id':
            continue
            
        try:
            std_val = metrics_df[col].std()
            if std_val < threshold:
                zero_var_metrics.append(col)
        except (TypeError, ValueError):
            # If column is not numeric, skip
            continue
            
    return zero_var_metrics

def save_metric_flags(zero_var_metrics: List[str], output_path: str) -> None:
    """
    Save zero-variance metric flags to a JSON file.
    
    Args:
        zero_var_metrics: List of metric names with zero variance
        output_path: Path to save the JSON file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    flags = {
        'non_informative_metrics': zero_var_metrics,
        'flag_reason': 'Zero variance detected (std < 1e-9)',
        'count': len(zero_var_metrics)
    }
    
    with open(output_path, 'w') as f:
        json.dump(flags, f, indent=2)

def analyze_and_flag_metrics(metrics_df: pd.DataFrame, output_path: str = 'data/processed/metric_flags.json') -> Dict[str, List[str]]:
    """
    Analyze metrics for zero variance and save flags to JSON.
    
    Args:
        metrics_df: DataFrame with computed metrics
        output_path: Path to save the metric flags JSON file
        
    Returns:
        Dict with 'non_informative_metrics' key containing list of flagged metrics
    """
    zero_var_metrics = detect_zero_variance_metrics(metrics_df)
    save_metric_flags(zero_var_metrics, output_path)
    
    return {
        'non_informative_metrics': zero_var_metrics
    }