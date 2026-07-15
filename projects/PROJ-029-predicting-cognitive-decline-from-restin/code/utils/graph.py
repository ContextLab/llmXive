"""
Graph utility functions for calculating network metrics.
"""
import numpy as np
import networkx as nx
from typing import Union, Tuple, Optional
import nibabel as nib
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def load_aal_atlas_mask(atlas_path: Union[str, Path]) -> np.ndarray:
    """Load AAL atlas mask from file."""
    atlas_path = Path(atlas_path)
    if not atlas_path.exists():
        raise FileNotFoundError(f"AAL atlas not found: {atlas_path}")
    
    img = nib.load(atlas_path)
    return img.get_fdata()

def validate_atlas_shape(mask: np.ndarray, expected_regions: int = 116) -> bool:
    """Validate that the atlas mask has the expected number of regions."""
    unique_regions = np.unique(mask)
    # Exclude 0 (background)
    unique_regions = unique_regions[unique_regions != 0]
    return len(unique_regions) == expected_regions

def create_graph_from_adjacency(adjacency_matrix: np.ndarray) -> nx.Graph:
    """Create a NetworkX graph from an adjacency matrix."""
    G = nx.from_numpy_array(adjacency_matrix, create_using=nx.Graph)
    return G

def calculate_degree_centrality(G: nx.Graph) -> float:
    """Calculate average degree centrality of the graph."""
    if G.number_of_nodes() == 0:
        return 0.0
    # Degree centrality is normalized by (n-1)
    deg_centrality = nx.degree_centrality(G)
    return float(np.mean(list(deg_centrality.values())))

def calculate_global_efficiency(G: nx.Graph) -> float:
    """Calculate global efficiency of the graph."""
    if G.number_of_nodes() <= 1:
        return 0.0
    try:
        return float(nx.global_efficiency(G))
    except nx.NetworkXError:
        # Handle disconnected graphs
        return 0.0

def calculate_clustering_coefficient(G: nx.Graph) -> float:
    """Calculate average clustering coefficient of the graph."""
    if G.number_of_nodes() == 0:
        return 0.0
    return float(nx.average_clustering(G))

def calculate_local_efficiency(G: nx.Graph) -> float:
    """Calculate local efficiency of the graph."""
    if G.number_of_nodes() <= 1:
        return 0.0
    try:
        return float(nx.local_efficiency(G))
    except nx.NetworkXError:
        return 0.0

def calculate_shortest_path_length(G: nx.Graph) -> float:
    """Calculate average shortest path length of the graph."""
    if G.number_of_nodes() <= 1:
        return 0.0
    try:
        # Check if graph is connected
        if not nx.is_connected(G):
            # For disconnected graphs, we might want to use average over components
            # or return NaN. Here we return average over largest component.
            largest_cc = max(nx.connected_components(G), key=len)
            subgraph = G.subgraph(largest_cc)
            return float(nx.average_shortest_path_length(subgraph))
        return float(nx.average_shortest_path_length(G))
    except nx.NetworkXError:
        return float('nan')
