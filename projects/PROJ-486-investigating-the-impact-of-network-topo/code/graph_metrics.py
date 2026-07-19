import numpy as np
import pandas as pd
import networkx as nx
from typing import Union, Dict, List, Optional
import json
import os
from config import RANDOM_SEED

def calculate_clustering_coefficient(adj_matrix: np.ndarray, weighted: bool = True) -> float:
    """
    Calculate the average clustering coefficient for a network.
    
    Args:
        adj_matrix: Adjacency matrix (numpy array). Can be weighted or binary.
        weighted: If True, treats the matrix as weighted for the calculation.
                
    Returns:
        Average clustering coefficient (float).
    """
    if weighted:
        G = nx.from_numpy_array(adj_matrix, create_using=nx.Graph)
        # NetworkX clustering for weighted graphs uses a specific definition
        # We'll use the standard weighted clustering coefficient
        try:
            coeffs = nx.clustering(G, weight='weight')
        except Exception:
            # Fallback to binary if weights cause issues
            binary_G = nx.from_numpy_array((adj_matrix > 0).astype(float), create_using=nx.Graph)
            coeffs = nx.clustering(binary_G)
    else:
        G = nx.from_numpy_array(adj_matrix, create_using=nx.Graph)
        coeffs = nx.clustering(G)
    
    return float(np.mean(list(coeffs.values())))

def calculate_path_length(adj_matrix: np.ndarray, weighted: bool = True) -> float:
    """
    Calculate the characteristic path length (average shortest path).
    
    Args:
        adj_matrix: Adjacency matrix (numpy array).
        weighted: If True, treats the matrix as weighted.
                
    Returns:
        Characteristic path length (float). Returns inf if graph is disconnected.
    """
    G = nx.from_numpy_array(adj_matrix, create_using=nx.Graph)
    
    # Check connectivity
    if not nx.is_connected(G):
        # For disconnected graphs, we might use the largest connected component
        # or return infinity. Here we use the largest connected component.
        largest_cc = max(nx.connected_components(G), key=len)
        subgraph = G.subgraph(largest_cc)
    else:
        subgraph = G
    
    try:
        path_lengths = nx.shortest_path_length(subgraph, weight='weight' if weighted else None)
        # Average of all path lengths
        total_len = 0.0
        count = 0
        for source, targets in path_lengths.items():
            for target, length in targets.items():
                if source != target:
                    total_len += length
                    count += 1
        
        if count == 0:
            return float('inf')
        
        return float(total_len / count)
    except nx.NetworkXError:
        return float('inf')

def compute_all_metrics(adj_matrix: np.ndarray) -> Dict[str, float]:
    """
    Compute all network metrics for a given adjacency matrix.
    
    Args:
        adj_matrix: Adjacency matrix (numpy array).
                
    Returns:
        Dictionary of metric names to values.
    """
    clustering = calculate_clustering_coefficient(adj_matrix)
    path_length = calculate_path_length(adj_matrix)
    
    return {
        'clustering_coefficient': clustering,
        'characteristic_path_length': path_length
    }

def process_subject_matrices(subject_data: pd.DataFrame) -> pd.DataFrame:
    """
    Process a dataframe of subject matrices and compute metrics.
    
    Args:
        subject_data: DataFrame with columns: subject_id, matrix_data (flattened upper triangle).
                
    Returns:
        DataFrame with added metric columns.
    """
    results = []
    
    for _, row in subject_data.iterrows():
        subject_id = row['subject_id']
        matrix_data = row['matrix_data']
        
        # Reconstruct matrix from upper triangle
        n = int((1 + np.sqrt(1 + 8 * len(matrix_data))) / 2)
        adj_matrix = np.zeros((n, n))
        
        # Fill upper triangle
        idx = 0
        for i in range(n):
            for j in range(i, n):
                adj_matrix[i, j] = matrix_data[idx]
                adj_matrix[j, i] = matrix_data[idx]
                idx += 1
        
        metrics = compute_all_metrics(adj_matrix)
        metrics['subject_id'] = subject_id
        results.append(metrics)
    
    return pd.DataFrame(results)

def detect_zero_variance_metrics(metrics_df: pd.DataFrame, threshold: float = 1e-9) -> List[Dict[str, str]]:
    """
    Detect metrics with zero variance and flag them as non-informative.
    
    Args:
        metrics_df: DataFrame containing metric columns.
        threshold: Variance threshold below which a metric is considered zero-variance.
                
    Returns:
        List of dictionaries with metric_name, status, and reason.
    """
    flags = []
    
    # Identify metric columns (exclude subject_id and other non-metric columns)
    metric_cols = [col for col in metrics_df.columns if col not in ['subject_id']]
    
    for col in metric_cols:
        if col in metrics_df.columns:
            std_val = metrics_df[col].std()
            if np.isnan(std_val) or std_val < threshold:
                flags.append({
                    'metric_name': col,
                    'status': 'Non-informative',
                    'reason': f'Zero variance detected (std={std_val:.2e} < {threshold})'
                })
    
    return flags

def save_metric_flags(flags: List[Dict[str, str]], output_path: str) -> None:
    """
    Save metric flags to a JSON file.
    
    Args:
        flags: List of flag dictionaries.
        output_path: Path to the output JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(flags, f, indent=2)

def analyze_and_flag_metrics(input_df_path: str, output_flags_path: str) -> List[Dict[str, str]]:
    """
    Load metrics, detect zero-variance, and save flags.
    
    Args:
        input_df_path: Path to the input CSV with metrics.
        output_flags_path: Path to save the flags JSON.
                
    Returns:
        List of detected flags.
    """
    if not os.path.exists(input_df_path):
        raise FileNotFoundError(f"Input file not found: {input_df_path}")
    
    metrics_df = pd.read_csv(input_df_path)
    flags = detect_zero_variance_metrics(metrics_df)
    save_metric_flags(flags, output_flags_path)
    
    return flags

def main():
    """Main entry point for graph metrics analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Compute and flag network metrics.')
    parser.add_argument('--input', type=str, required=True, help='Input CSV with matrices or precomputed metrics.')
    parser.add_argument('--output-flags', type=str, default='data/processed/metric_flags.json', help='Output path for flags.')
    parser.add_argument('--output-metrics', type=str, default='data/processed/topology_metrics.csv', help='Output path for computed metrics.')
    parser.add_argument('--mode', type=str, choices=['matrices', 'metrics'], default='metrics', help='Input mode.')
    
    args = parser.parse_args()
    
    if args.mode == 'matrices':
        # Process raw matrices to compute metrics
        raw_df = pd.read_csv(args.input)
        metrics_df = process_subject_matrices(raw_df)
        metrics_df.to_csv(args.output_metrics, index=False)
        
        # Then flag zero-variance
        flags = analyze_and_flag_metrics(args.output_metrics, args.output_flags)
    else:
        # Assume input is already metrics
        flags = analyze_and_flag_metrics(args.input, args.output_flags)
    
    print(f"Flags saved to {args.output_flags}")
    print(f"Total flags: {len(flags)}")
    for flag in flags:
        print(f"  - {flag['metric_name']}: {flag['status']} ({flag['reason']})")

if __name__ == '__main__':
    main()
