import numpy as np
import pandas as pd
import networkx as nx
from typing import Union, Dict, List, Optional
import json
import os

from config import get_atlas_path, get_atlas_node_count

def calculate_clustering_coefficient(correlation_matrix: np.ndarray) -> float:
    """
    Calculate the weighted clustering coefficient for a correlation matrix.
    
    Args:
        correlation_matrix: Square 2D numpy array representing correlation matrix.
        
    Returns:
        Average clustering coefficient across all nodes.
    """
    if correlation_matrix.shape[0] != correlation_matrix.shape[1]:
        raise ValueError("Correlation matrix must be square")
    
    # Create a weighted graph from the correlation matrix
    G = nx.from_numpy_array(correlation_matrix)
    
    # Calculate weighted clustering coefficient
    clustering_coeffs = nx.clustering(G, weight='weight')
    
    if not clustering_coeffs:
        return 0.0
        
    return float(np.mean(list(clustering_coeffs.values())))

def calculate_path_length(correlation_matrix: np.ndarray) -> float:
    """
    Calculate the characteristic path length for a correlation matrix.
    
    Args:
        correlation_matrix: Square 2D numpy array representing correlation matrix.
        
    Returns:
        Characteristic path length of the network.
    """
    if correlation_matrix.shape[0] != correlation_matrix.shape[1]:
        raise ValueError("Correlation matrix must be square")
    
    # Create a weighted graph
    G = nx.from_numpy_array(correlation_matrix)
    
    # For correlation matrices, we often convert to distance by 1-r or similar
    # But for path length, we need positive weights. We'll use a threshold or transformation.
    # Here we use a simple approach: treat high correlation as short distance.
    # We'll use 1 - correlation as distance, but handle self-loops and negative values.
    
    # Convert to distance matrix (1 - correlation), ensuring non-negative
    distance_matrix = 1.0 - correlation_matrix
    np.fill_diagonal(distance_matrix, 0)
    distance_matrix = np.maximum(distance_matrix, 1e-9)  # Avoid division by zero
    
    # Reconstruct graph with distance weights
    G_dist = nx.from_numpy_array(distance_matrix)
    
    # Calculate average shortest path length
    try:
        path_lengths = nx.all_pairs_shortest_path_length(G_dist)
        # Flatten and average
        total_length = 0.0
        count = 0
        for source, lengths in path_lengths:
            for target, length in lengths.items():
                if source != target:
                    total_length += length
                    count += 1
        
        if count == 0:
            return float('inf')
            
        return float(total_length / count)
    except nx.NetworkXError:
        # Graph might be disconnected
        return float('inf')

def compute_all_metrics(correlation_matrix: np.ndarray) -> Dict[str, float]:
    """
    Compute all network metrics for a given correlation matrix.
    
    Args:
        correlation_matrix: Square 2D numpy array representing correlation matrix.
        
    Returns:
        Dictionary with metric names as keys and computed values as values.
    """
    metrics = {}
    metrics['clustering_coefficient'] = calculate_clustering_coefficient(correlation_matrix)
    metrics['characteristic_path_length'] = calculate_path_length(correlation_matrix)
    return metrics

def process_subject_matrices(subject_data: pd.DataFrame) -> pd.DataFrame:
    """
    Process subject correlation matrices and compute network metrics.
    
    Args:
        subject_data: DataFrame with subject_id and correlation matrix data.
        
    Returns:
        DataFrame with subject_id and computed network metrics.
    """
    results = []
    
    for _, row in subject_data.iterrows():
        subject_id = row['subject_id']
        
        # Extract correlation matrix (assuming it's stored as a flattened array or similar)
        # This is a placeholder implementation - actual extraction depends on data format
        if 'correlation_matrix' in row:
            corr_matrix = row['correlation_matrix']
            if isinstance(corr_matrix, str):
                # Try to parse from string representation
                corr_matrix = eval(corr_matrix)
            corr_matrix = np.array(corr_matrix)
            
            metrics = compute_all_metrics(corr_matrix)
            metrics['subject_id'] = subject_id
            results.append(metrics)
    
    return pd.DataFrame(results) if results else pd.DataFrame()

def detect_zero_variance_metrics(metrics_df: pd.DataFrame, threshold: float = 1e-9) -> Dict[str, List[str]]:
    """
    Detect metrics with zero variance across subjects.
    
    Args:
        metrics_df: DataFrame with metric columns.
        threshold: Variance threshold below which a metric is considered zero-variance.
        
    Returns:
        Dictionary with 'non_informative' key containing list of metric names.
    """
    metric_columns = ['clustering_coefficient', 'characteristic_path_length']
    non_informative_metrics = []
    
    for col in metric_columns:
        if col in metrics_df.columns:
            std_val = metrics_df[col].std()
            if std_val < threshold:
                non_informative_metrics.append(col)
    
    return {'non_informative': non_informative_metrics}

def save_metric_flags(flags: Dict[str, List[str]], output_path: str) -> None:
    """
    Save metric flags to a JSON file.
    
    Args:
        flags: Dictionary containing metric flags.
        output_path: Path to save the JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(flags, f, indent=2)

def analyze_and_flag_metrics(input_path: str, output_path: str) -> Dict[str, List[str]]:
    """
    Main function to compute metrics, detect zero variance, and save flags.
    
    Args:
        input_path: Path to the input CSV with computed metrics.
        output_path: Path to save the metric flags JSON.
        
    Returns:
        Dictionary containing the metric flags.
    """
    # Load the metrics data
    if not os.path.exists(input_path):
        # If input doesn't exist, create empty flags
        flags = {'non_informative': []}
        save_metric_flags(flags, output_path)
        return flags
    
    metrics_df = pd.read_csv(input_path)
    
    # Detect zero variance metrics
    flags = detect_zero_variance_metrics(metrics_df)
    
    # Save flags
    save_metric_flags(flags, output_path)
    
    return flags

# For backward compatibility and direct execution
if __name__ == "__main__":
    # Example usage for testing
    import sys
    if len(sys.argv) >= 3:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        flags = analyze_and_flag_metrics(input_file, output_file)
        print(f"Metric flags saved to {output_file}: {flags}")
    else:
        print("Usage: python graph_metrics.py <input_csv> <output_json>")