import networkx as nx
import logging
from typing import Dict, Any, List, Tuple, Optional, Union
from data_models import NetworkGraph

logger = logging.getLogger(__name__)

def compute_metrics(edges: List[Tuple[int, int]], n_nodes: int) -> Dict[str, float]:
    """
    Compute topological metrics: degree distribution, clustering coefficient, average path length.
    Handles disconnected graphs by returning infinity for path length.
    """
    if n_nodes == 0:
        return {
            "degree_mean": 0.0,
            "degree_std": 0.0,
            "clustering_coefficient": 0.0,
            "average_path_length": float('inf'),
            "connectivity": False
        }

    G = nx.Graph()
    G.add_nodes_from(range(n_nodes))
    G.add_edges_from(edges)

    is_connected = nx.is_connected(G)
    
    # Degree distribution stats
    degrees = [d for _, d in G.degree()]
    degree_mean = np.mean(degrees) if degrees else 0.0
    degree_std = np.std(degrees) if degrees else 0.0

    # Clustering coefficient
    clustering = nx.average_clustering(G)

    # Average path length
    if is_connected:
        avg_path = nx.average_shortest_path_length(G)
    else:
        avg_path = float('inf')

    return {
        "degree_mean": float(degree_mean),
        "degree_std": float(degree_std),
        "clustering_coefficient": float(clustering),
        "average_path_length": float(avg_path),
        "connectivity": is_connected
    }
