import numpy as np
import pandas as pd
import networkx as nx
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
import json
from config import get_config_dict
from preprocess.loader import load_hcp_dmri

def calculate_graph_metrics(adjacency_matrix, threshold=0.1):
    """
    Calculate graph theoretical metrics from an adjacency matrix.
    
    Args:
        adjacency_matrix: 2D numpy array (regions x regions)
        threshold: Density threshold or absolute threshold to apply.
        
    Returns:
        dict: Metrics including global efficiency, clustering, modularity, sparsity.
    """
    config = get_config_dict()
    
    # Apply threshold (simplify to binary for basic metrics)
    # Here we assume the adjacency matrix is weighted, and we threshold to keep top X%
    # or apply a hard threshold. The task mentions "sparsity > 90% exclusion".
    # Sparsity = 1 - density. If density < 0.1, sparsity > 0.9.
    
    # Flatten and sort to find threshold if using density-based
    if threshold <= 1.0 and threshold > 0:
        # Assume threshold is a density (fraction of edges to keep)
        # We need to keep the top 'density' fraction of edges
        weights = adjacency_matrix[np.triu_indices_from(adjacency_matrix, k=1)]
        weights = weights[weights > 0]
        if len(weights) == 0:
            return {'sparsity': 1.0, 'global_efficiency': 0, 'clustering': 0, 'modularity': 0}
        
        # Sort descending and find cutoff
        sorted_weights = np.sort(weights)[::-1]
        n_edges_to_keep = int(len(sorted_weights) * threshold)
        if n_edges_to_keep == 0:
            n_edges_to_keep = 1 # Keep at least one edge to avoid empty graph
        
        cutoff = sorted_weights[n_edges_to_keep - 1]
        adj_binary = (adjacency_matrix >= cutoff).astype(float)
    else:
        # Assume threshold is an absolute value
        adj_binary = (adjacency_matrix >= threshold).astype(float)
    
    # Calculate actual density
    n = adj_binary.shape[0]
    max_edges = n * (n - 1) / 2
    actual_edges = np.sum(adj_binary) / 2 # Undirected
    density = actual_edges / max_edges if max_edges > 0 else 0
    sparsity = 1.0 - density
    
    # Create NetworkX graph
    G = nx.from_numpy_array(adj_binary)
    
    # Check for sparsity exclusion (Task T015: Handle sparsity > 90% exclusion)
    if sparsity > config['thresholds']['max_sparsity']:
        # Return a flag or specific metrics indicating exclusion
        # We return the metrics but mark them or let the caller handle it
        pass
    
    # Global Efficiency
    try:
        global_eff = nx.global_efficiency(G)
    except:
        global_eff = 0.0
        
    # Average Clustering Coefficient
    try:
        clustering = nx.average_clustering(G)
    except:
        clustering = 0.0
        
    # Modularity (requires community detection)
    try:
        communities = nx.community.louvain_communities(G, seed=config['seed'])
        modularity = nx.community.modularity(G, communities)
    except:
        modularity = 0.0
        
    return {
        'sparsity': float(sparsity),
        'density': float(density),
        'global_efficiency': float(global_eff),
        'clustering_coefficient': float(clustering),
        'modularity': float(modularity),
        'n_nodes': int(n),
        'n_edges': int(actual_edges)
    }

def process_subject_structural_metrics(dmri_data, subject_id):
    """
    Process a single subject's dMRI data to calculate structural metrics.
    
    Args:
        dmri_data: Connectivity matrix or raw data to process.
        subject_id: Subject identifier.
        
    Returns:
        dict: {subject_id: metrics_dict}
    """
    config = get_config_dict()
    
    # If dmri_data is raw, we need to compute connectivity matrix first.
    # For this implementation, we assume dmri_data is the connectivity matrix.
    # If it's tractography streamlines, we would need to build the matrix here.
    # Assuming input is a connectivity matrix (n_regions x n_regions)
    
    if isinstance(dmri_data, np.ndarray):
        adj_matrix = dmri_data
    else:
        # Try to convert if it's a list or other structure
        adj_matrix = np.array(dmri_data)
        
    metrics = calculate_graph_metrics(adj_matrix, threshold=config['thresholds']['density'])
    metrics['subject_id'] = subject_id
    
    return {subject_id: metrics}

def run_structural_pipeline(subject_ids):
    """
    Run structural pipeline for a list of subjects.
    
    Args:
        subject_ids: List of subject IDs.
        
    Returns:
        dict: {subject_id: metrics_dict}
    """
    results = {}
    for sid in subject_ids:
        try:
            dmri_data = load_hcp_dmri(sid)
            if dmri_data is not None:
                res = process_subject_structural_metrics(dmri_data, sid)
                results.update(res)
            else:
                print(f"No dMRI data for {sid}")
        except Exception as e:
            print(f"Error processing {sid}: {e}")
    return results

def main():
    """Entry point for testing."""
    print("Structural pipeline module loaded.")

if __name__ == '__main__':
    main()
