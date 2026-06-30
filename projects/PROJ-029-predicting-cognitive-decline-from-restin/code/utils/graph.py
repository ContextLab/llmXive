"""
Graph utility functions for network topology analysis.

Implements loading of AAL atlas, creation of graphs from adjacency matrices,
and calculation of standard graph metrics (degree, efficiency, clustering, etc.).
"""
import numpy as np
import networkx as nx
from typing import Union, Tuple, Optional
import nibabel as nib
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def load_aal_atlas_mask(atlas_path: Union[str, Path]) -> np.ndarray:
    """
    Load the AAL atlas mask from a NIfTI file.
    
    Args:
        atlas_path: Path to the AAL atlas NIfTI file.
        
    Returns:
        np.ndarray: 3D array representing the atlas mask with integer labels.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        Exception: If the file is not a valid NIfTI image.
    """
    path = Path(atlas_path)
    if not path.exists():
        raise FileNotFoundError(f"AAL atlas file not found: {path}")
    
    try:
        img = nib.load(path)
        mask_data = img.get_fdata(dtype=np.int16)
        logger.info(f"Loaded AAL atlas from {path}. Shape: {mask_data.shape}")
        return mask_data
    except Exception as e:
        logger.error(f"Failed to load AAL atlas from {path}: {e}")
        raise

def create_graph_from_adjacency(adjacency_matrix: np.ndarray) -> nx.Graph:
    """
    Create a NetworkX graph from an adjacency matrix.
    
    Args:
        adjacency_matrix: 2D numpy array representing the adjacency matrix.
        
    Returns:
        nx.Graph: The created graph.
    """
    G = nx.Graph()
    n_nodes = adjacency_matrix.shape[0]
    
    # Add nodes
    for i in range(n_nodes):
        G.add_node(i)
        
    # Add edges
    for i in range(n_nodes):
        for j in range(i + 1, n_nodes):
            weight = adjacency_matrix[i, j]
            if weight > 0:
                G.add_edge(i, j, weight=weight)
                
    logger.debug(f"Created graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    return G

def calculate_global_efficiency(G: nx.Graph) -> float:
    """
    Calculate the global efficiency of a graph.
    
    Args:
        G: NetworkX graph.
        
    Returns:
        float: Global efficiency value.
    """
    if G.number_of_nodes() == 0:
        return 0.0
    return nx.global_efficiency(G)

def calculate_clustering_coefficient(G: nx.Graph) -> float:
    """
    Calculate the average clustering coefficient of a graph.
    
    Args:
        G: NetworkX graph.
        
    Returns:
        float: Average clustering coefficient.
    """
    if G.number_of_nodes() == 0:
        return 0.0
    return nx.average_clustering(G)

def calculate_degree_centrality(G: nx.Graph) -> dict:
    """
    Calculate the degree centrality for all nodes in a graph.
    
    Args:
        G: NetworkX graph.
        
    Returns:
        dict: Dictionary mapping node to degree centrality.
    """
    return nx.degree_centrality(G)

def calculate_local_efficiency(G: nx.Graph) -> float:
    """
    Calculate the local efficiency of a graph.
    
    Args:
        G: NetworkX graph.
        
    Returns:
        float: Local efficiency value.
    """
    if G.number_of_nodes() == 0:
        return 0.0
    return nx.local_efficiency(G)

def calculate_shortest_path_length(G: nx.Graph) -> float:
    """
    Calculate the average shortest path length of a graph.
    
    Args:
        G: NetworkX graph.
        
    Returns:
        float: Average shortest path length. Returns infinity if graph is disconnected.
    """
    if G.number_of_nodes() == 0:
        return 0.0
    try:
        return nx.average_shortest_path_length(G)
    except nx.NetworkXError:
        # Graph is disconnected
        return float('inf')
