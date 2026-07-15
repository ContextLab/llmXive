"""
Graph theory utilities for network analysis of fMRI connectivity matrices.

Implements standard graph-theoretical measures including:
- Degree centrality
- Global efficiency
- Clustering coefficient
- Shortest path length
"""
from __future__ import annotations

import numpy as np
import networkx as nx
from typing import Union, Tuple, Optional
import nibabel as nib
from pathlib import Path
import logging

# Configure logging
logger = logging.getLogger(__name__)


def load_aal_atlas_mask(atlas_path: Union[str, Path]) -> np.ndarray:
    """
    Load AAL atlas mask from file.
    
    Args:
        atlas_path: Path to the AAL atlas file (NIfTI format)
        
    Returns:
        3D numpy array representing the atlas mask
    """
  #   atlas_path = Path(atlas_path)
    if not atlas_path.exists():
        raise FileNotFoundError(f"AAL atlas file not found: {atlas_path}")
    
    try:
        atlas_img = nib.load(str(atlas_path))
        atlas_mask = atlas_img.get_fdata()
        return atlas_mask
    except Exception as e:
        logger.error(f"Failed to load AAL atlas: {e}")
        raise


def validate_atlas_shape(atlas_mask: np.ndarray, expected_shape: Tuple[int, ...]) -> bool:
    """
    Validate that the atlas mask has the expected shape.
    
    Args:
        atlas_mask: 3D numpy array of the atlas
        expected_shape: Expected shape tuple (x, y, z)
        
    Returns:
        True if valid, False otherwise
    """
    if atlas_mask.ndim != 3:
        logger.error(f"Expected 3D atlas, got {atlas_mask.ndim}D")
        return False
    
    if atlas_mask.shape != expected_shape:
        logger.warning(f"Atlas shape mismatch: expected {expected_shape}, got {atlas_mask.shape}")
        return False
    
    return True


def create_graph_from_adjacency(adjacency_matrix: np.ndarray) -> nx.Graph:
    """
    Create a NetworkX graph from an adjacency matrix.
    
    Args:
        adjacency_matrix: 2D numpy array representing the adjacency matrix
        
    Returns:
        NetworkX Graph object
    """
    if adjacency_matrix.ndim != 2:
        raise ValueError(f"Expected 2D adjacency matrix, got {adjacency_matrix.ndim}D")
    
    if adjacency_matrix.shape[0] != adjacency_matrix.shape[1]:
        raise ValueError("Adjacency matrix must be square")
    
    G = nx.from_numpy_array(adjacency_matrix, create_using=nx.Graph)
    return G


def calculate_degree_centrality(G: nx.Graph) -> np.ndarray:
    """
    Calculate degree centrality for all nodes in the graph.
    
    Degree centrality is the fraction of nodes a node is connected to.
    
    Args:
        G: NetworkX Graph object
        
    Returns:
        1D numpy array of degree centrality values for each node
    """
    centrality = nx.degree_centrality(G)
    # Convert to array ordered by node index
    nodes = sorted(G.nodes())
    return np.array([centrality[node] for node in nodes])


def calculate_global_efficiency(G: nx.Graph) -> float:
    """
    Calculate global efficiency of the graph.
    
    Global efficiency is the average inverse shortest path length.
    It measures the efficiency of parallel information transfer.
    
    Args:
        G: NetworkX Graph object
        
    Returns:
        Global efficiency value (float)
    """
    if len(G.nodes()) == 0:
        return 0.0
    
    try:
        efficiency = nx.global_efficiency(G)
        return float(efficiency)
    except nx.NetworkXError:
        # Handle disconnected graphs
        return 0.0


def calculate_clustering_coefficient(G: nx.Graph) -> float:
    """
    Calculate the average clustering coefficient of the graph.
    
    The clustering coefficient measures the degree to which nodes in a graph
    tend to cluster together.
    
    Args:
        G: NetworkX Graph object
        
    Returns:
        Average clustering coefficient (float)
    """
    if len(G.nodes()) == 0:
        return 0.0
    
    try:
      #   cc = nx.clustering(G)
      #   return float(np.mean(list(cc.values())))
        return float(nx.average_clustering(G))
    except nx.NetworkXError:
        return 0.0


def calculate_local_efficiency(G: nx.Graph) -> float:
    """
    Calculate local efficiency of the graph.
    
    Local efficiency is the global efficiency computed on the local neighborhood
    of each node.
    
    Args:
        G: NetworkX Graph object
        
    Returns:
        Local efficiency value (float)
    """
    if len(G.nodes()) == 0:
        return 0.0
    
    try:
        efficiency = nx.local_efficiency(G)
        return float(efficiency)
    except nx.NetworkXError:
        return 0.0


def calculate_shortest_path_length(G: nx.Graph) -> float:
    """
    Calculate the average shortest path length of the graph.
    
    Args:
        G: NetworkX Graph object
        
    Returns:
        Average shortest path length (float)
    """
    if len(G.nodes()) == 0:
        return 0.0
    
    try:
      #   # Handle disconnected graphs by computing efficiency on largest component
      #   if not nx.is_connected(G):
      #       largest_cc = max(nx.connected_components(G), key=len)
      #       G_sub = G.subgraph(largest_cc)
      #   else:
      #       G_sub = G
      #   
      #   length = nx.average_shortest_path_length(G_sub)
      #   return float(length)
        # Use efficiency for disconnected graphs
        return float(nx.average_shortest_path_length(G))
    except nx.NetworkXError:
        # For disconnected graphs, return efficiency-based metric
        return float(nx.global_efficiency(G))


def create_minimal_atlas(num_regions: int = 90) -> np.ndarray:
    """
    Create a minimal synthetic atlas for testing.
    
    Args:
        num_regions: Number of regions in the atlas
        
    Returns:
        3D array representing a minimal atlas
    """
    # Create a simple 3D grid with unique labels
    size = int(np.ceil(num_regions ** (1/3))) + 1
    atlas = np.zeros((size, size, size), dtype=np.int32)
    
    label = 1
    for x in range(size):
        for y in range(size):
            for z in range(size):
                if label <= num_regions:
                    atlas[x, y, z] = label
                    label += 1
                else:
                    break
            if label > num_regions:
                break
        if label > num_regions:
            break
    
    return atlas
