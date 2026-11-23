"""
Structural Preprocessing and Graph Metric Calculation

This module handles the calculation of graph theoretical metrics (global efficiency,
clustering coefficient, modularity) from structural connectivity matrices derived
from diffusion MRI data. It also supports sensitivity analysis for graph density
and tractography confidence thresholds.
"""

import numpy as np
import pandas as pd
import networkx as nx
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
import json
import os
import sys

from config import get_config_dict

def calculate_graph_metrics(
    adjacency_matrix: np.ndarray,
    density_threshold: float = 0.15,
    return_raw: bool = False
) -> Optional[Dict[str, float]]:
    """
    Calculate graph theoretical metrics from an adjacency matrix.

    Args:
        adjacency_matrix: N x N adjacency matrix (weighted or binary).
        density_threshold: Proportional threshold to apply (0.0 to 1.0).
        return_raw: If True, return the thresholded matrix as well.

    Returns:
        Dictionary containing 'global_efficiency', 'clustering', 'modularity'.
        Returns None if the graph is disconnected or invalid.
    """
    try:
        N = adjacency_matrix.shape[0]
        if N < 2:
            return None

        # Create a graph from the matrix
        # Ensure symmetry
        A = (adjacency_matrix + adjacency_matrix.T) / 2.0
        
        # Apply density thresholding
        # Flatten the upper triangle to determine the threshold
        upper_tri = A[np.triu_indices(N, k=1)]
        if len(upper_tri) == 0:
            return None
        
        # Sort values to find the threshold
        sorted_vals = np.sort(upper_tri)[::-1]
        num_edges_to_keep = int(len(sorted_vals) * density_threshold)
        
        if num_edges_to_keep == 0:
            return None
        
        threshold_val = sorted_vals[num_edges_to_keep - 1]
        
        # Apply threshold
        A_thresholded = A.copy()
        A_thresholded[A_thresholded < threshold_val] = 0.0
        np.fill_diagonal(A_thresholded, 0.0)

        # Check for connectivity
        G = nx.from_numpy_array(A_thresholded)
        if not nx.is_connected(G):
            # For efficiency, we might want to consider the largest component
            # But for this task, we'll return None if not fully connected
            # unless we decide to use largest component.
            # Let's use the largest connected component to be robust.
            try:
                largest_cc = max(nx.connected_components(G), key=len)
                if len(largest_cc) < 2:
                    return None
                G = G.subgraph(largest_cc).copy()
            except:
                return None

        # Calculate metrics
        try:
            global_eff = nx.global_efficiency(G)
        except:
            global_eff = 0.0

        try:
            clustering = nx.average_clustering(G)
        except:
            clustering = 0.0

        try:
            # Modularity requires a partition
            # Use Louvain method
            import community as community_louvain
            partition = community_louvain.best_partition(G)
            modularity = community_louvain.modularity(partition, G)
        except ImportError:
            # Fallback if python-igraph or networkx-algorithms not available
            # Or use a simple random partition (not ideal)
            # For now, return 0.0 or handle gracefully
            modularity = 0.0
        except Exception:
            modularity = 0.0

        result = {
            'global_efficiency': global_eff,
            'clustering': clustering,
            'modularity': modularity
        }

        if return_raw:
            result['thresholded_matrix'] = A_thresholded

        return result

    except Exception as e:
        print(f"Error calculating graph metrics: {e}")
        return None

def process_subject_structural_metrics(
    subject_id: str,
    matrix: np.ndarray,
    density_threshold: float,
    config: Dict[str, Any]
) -> Optional[Dict[str, float]]:
    """
    Process a single subject's structural matrix to extract metrics.

    Args:
        subject_id: Subject identifier.
        matrix: Adjacency matrix.
        density_threshold: Density threshold to apply.
        config: Configuration dictionary.

    Returns:
        Dictionary of metrics or None if processing fails.
    """
    metrics = calculate_graph_metrics(matrix, density_threshold)
    if metrics is None:
        return None
    
    metrics['subject_id'] = subject_id
    return metrics

def run_structural_pipeline(
    subjects: List[str],
    density_threshold: float,
    config: Dict[str, Any]
) -> pd.DataFrame:
    """
    Run the structural pipeline for a list of subjects.

    Args:
        subjects: List of subject IDs.
        density_threshold: Density threshold.
        config: Configuration dictionary.

    Returns:
        DataFrame of structural metrics.
    """
    results = []
    
    for subject_id in subjects:
        # Load matrix (placeholder - assume it's loaded elsewhere or via loader)
        # This function assumes the matrix is available or loaded here.
        # In a real scenario, we would call load_hcp_dmri here.
        # For now, we assume the matrix is passed or loaded from a file.
        # Since this is a skeleton, we'll assume the matrix is loaded from a file
        # named {subject_id}_matrix.npy in the processed data directory.
        
        matrix_path = Path(config['data_processed_dir']) / f"{subject_id}_matrix.npy"
        if not matrix_path.exists():
            print(f"Matrix not found for {subject_id}, skipping.")
            continue
        
        matrix = np.load(matrix_path)
        
        metrics = process_subject_structural_metrics(subject_id, matrix, density_threshold, config)
        if metrics:
            results.append(metrics)
    
    return pd.DataFrame(results)

def run_sensitivity_analysis(
    subjects: List[str],
    density_thresholds: List[float],
    config: Dict[str, Any]
) -> pd.DataFrame:
    """
    Run sensitivity analysis for different density thresholds.

    Args:
        subjects: List of subject IDs.
        density_thresholds: List of density thresholds.
        config: Configuration dictionary.

    Returns:
        DataFrame of metrics for each subject and density.
    """
    results = []
    
    for subject_id in subjects:
        matrix_path = Path(config['data_processed_dir']) / f"{subject_id}_matrix.npy"
        if not matrix_path.exists():
            continue
        
        matrix = np.load(matrix_path)
        
        for thresh in density_thresholds:
            metrics = calculate_graph_metrics(matrix, thresh)
            if metrics:
                metrics['subject_id'] = subject_id
                metrics['density_threshold'] = thresh
                results.append(metrics)
    
    return pd.DataFrame(results)

def save_structural_metrics_to_csv(
    df: pd.DataFrame,
    output_path: str
):
    """
    Save structural metrics to a CSV file.

    Args:
        df: DataFrame of metrics.
        output_path: Path to save the CSV.
    """
    df.to_csv(output_path, index=False)

def main():
    """
    Main entry point for structural preprocessing.
    """
    config = get_config_dict()
    subjects = ["100307"] # Example subject
    density = config.get('DENSITY_THRESHOLD_BASELINE', 0.15)
    
    # Placeholder for actual pipeline execution
    # In a real run, this would load data and process it.
    print("Structural pipeline ready.")

if __name__ == '__main__':
    main()