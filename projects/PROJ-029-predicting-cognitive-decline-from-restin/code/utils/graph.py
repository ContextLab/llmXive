import numpy as np
import networkx as nx
from typing import Union, Tuple, Optional
import nibabel as nib
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def load_aal_atlas_mask(atlas_path: Union[str, Path]) -> np.ndarray:
    """Load the AAL atlas mask.
    
    Args:
        atlas_path: Path to the AAL atlas NIfTI file.
        
    Returns:
        3D numpy array of the atlas mask.
    """
    atlas_path = Path(atlas_path)
    if not atlas_path.exists():
        raise FileNotFoundError(f"AAL atlas not found at {atlas_path}")
    
    img = nib.load(atlas_path)
    return img.get_fdata()


def validate_atlas_shape(mask: np.ndarray, expected_regions: int = 90) -> bool:
    """Validate that the atlas mask has the expected number of regions."""
    unique_regions = np.unique(mask)
    # Filter out background (0)
    regions = unique_regions[unique_regions > 0]
    return len(regions) >= expected_regions


def create_graph_from_adjacency(adjacency_matrix: np.ndarray) -> nx.Graph:
    """Create a NetworkX graph from an adjacency matrix.
    
    Args:
        adjacency_matrix: Square adjacency matrix (weighted or unweighted).
        
    Returns:
        NetworkX graph object.
    """
    G = nx.Graph()
    n = adjacency_matrix.shape[0]
    G.add_nodes_from(range(n))
    
    # Add edges for non-zero entries (upper triangle to avoid duplicates)
    for i in range(n):
        for j in range(i + 1, n):
            weight = adjacency_matrix[i, j]
            if weight != 0:
                G.add_edge(i, j, weight=weight)
                
    return G


def calculate_global_efficiency(G: nx.Graph) -> float:
    """Calculate the global efficiency of the graph.
    
    Args:
        G: NetworkX graph.
        
    Returns:
        Global efficiency value.
    """
    if G.number_of_nodes() == 0:
        return 0.0
    try:
        return nx.global_efficiency(G)
    except Exception:
        # Fallback for disconnected graphs
        return 0.0


def calculate_clustering_coefficient(G: nx.Graph) -> dict:
    """Calculate the clustering coefficient for each node.
    
    Args:
        G: NetworkX graph.
        
    Returns:
        Dictionary mapping node to clustering coefficient.
    """
    return nx.clustering(G)


def calculate_degree_centrality(G: nx.Graph) -> dict:
    """Calculate the degree centrality for each node.
    
    Args:
        G: NetworkX graph.
        
    Returns:
        Dictionary mapping node to degree centrality.
    """
    return nx.degree_centrality(G)


def calculate_local_efficiency(G: nx.Graph) -> float:
    """Calculate the local efficiency of the graph.
    
    Args:
        G: NetworkX graph.
        
    Returns:
        Local efficiency value.
    """
    if G.number_of_nodes() == 0:
        return 0.0
    try:
        return nx.local_efficiency(G)
    except Exception:
        return 0.0


def calculate_shortest_path_length(G: nx.Graph) -> Union[float, dict]:
    """Calculate the average shortest path length.
    
    Args:
        G: NetworkX graph.
        
    Returns:
        Average shortest path length or dictionary of shortest paths.
    """
    if G.number_of_nodes() == 0:
        return 0.0
    try:
        return nx.average_shortest_path_length(G)
    except nx.NetworkXError:
        # Handle disconnected graphs
        if nx.is_connected(G):
            return nx.average_shortest_path_length(G)
        else:
            # Calculate for largest connected component
            largest_cc = max(nx.connected_components(G), key=len)
            subG = G.subgraph(largest_cc)
            return nx.average_shortest_path_length(subG)
