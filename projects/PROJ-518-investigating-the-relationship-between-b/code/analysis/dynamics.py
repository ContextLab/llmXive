"""
Dynamic network analysis functions for brain network dynamics.
"""
from typing import List
import numpy as np
import networkx as nx

def detect_communities(connectivity_matrix: np.ndarray, gamma: float = 1.0) -> List[int]:
    """
    Detect communities in a connectivity matrix using Louvain algorithm.
    
    Args:
        connectivity_matrix: Correlation matrix (n_rois x n_rois)
        gamma: Resolution parameter for Louvain algorithm (default 1.0)
    
    Returns:
        List of community labels for each ROI
    """
    # Create weighted graph from correlation matrix
    G = nx.Graph()
    n_nodes = connectivity_matrix.shape[0]
    
    # Add edges with weights (only positive correlations)
    for i in range(n_nodes):
        for j in range(i + 1, n_nodes):
            weight = connectivity_matrix[i, j]
            if weight > 0:
                G.add_edge(i, j, weight=weight)
    
    # Detect communities using Louvain algorithm
    try:
        communities = nx.community.louvain_communities(G, resolution=gamma)
    except AttributeError:
        # Fallback for older networkx versions
        communities = nx.community.louvain_communities(G, resolution=gamma)
    
    # Convert to label array
    labels = [0] * n_nodes
    for community_idx, community in enumerate(communities):
        for node in community:
            labels[node] = community_idx
    
    return labels

def calculate_flexibility(community_labels: List[List[int]]) -> float:
    """
    Calculate network flexibility from community labels across windows.
    
    Counts ROI community changes and averages across ROIs to produce
    the whole-brain metric.
    
    Args:
        community_labels: List of community label arrays (one per window)
    
    Returns:
        Average flexibility across all ROIs
    """
    if len(community_labels) < 2:
        return 0.0
    
    n_windows = len(community_labels)
    n_rois = len(community_labels[0])
    
    # Count community changes for each ROI
    changes_per_roi = []
    
    for roi_idx in range(n_rois):
        changes = 0
        for window_idx in range(1, n_windows):
            if community_labels[window_idx][roi_idx] != community_labels[window_idx - 1][roi_idx]:
                changes += 1
        
        # Normalize by maximum possible changes
        max_changes = n_windows - 1
        flexibility_roi = changes / max_changes if max_changes > 0 else 0
        changes_per_roi.append(flexibility_roi)
    
    # Average across ROIs
    avg_flexibility = np.mean(changes_per_roi)
    
    return float(avg_flexibility)