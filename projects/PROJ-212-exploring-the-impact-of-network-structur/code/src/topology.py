import networkx as nx
import logging
from typing import Dict, Any, List, Tuple, Optional, Union
from data_models import NetworkGraph
import numpy as np
import math

logger = logging.getLogger(__name__)

def compute_metrics(graph: Union[nx.Graph, NetworkGraph]) -> Dict[str, Any]:
    """
    Compute topological metrics for a given network graph.

    Metrics computed:
    - degree_distribution: Dict mapping degree to frequency
    - mean_degree: float
    - clustering_coefficient: float (average local clustering)
    - average_path_length: float (infinity if graph is disconnected)
    - num_nodes: int
    - num_edges: int
    - is_connected: bool

    Args:
        graph: A NetworkX graph or NetworkGraph dataclass instance.

    Returns:
        Dictionary containing the computed metrics.
    """
    # Handle NetworkGraph wrapper if passed
    if isinstance(graph, NetworkGraph):
        nx_graph = graph.graph
    else:
        nx_graph = graph

    if nx_graph is None:
        logger.error("Graph is None")
        return {
            "degree_distribution": {},
            "mean_degree": 0.0,
            "clustering_coefficient": 0.0,
            "average_path_length": float('inf'),
            "num_nodes": 0,
            "num_edges": 0,
            "is_connected": False
        }

    num_nodes = nx_graph.number_of_nodes()
    num_edges = nx_graph.number_of_edges()

    # Degree Distribution
    degrees = [d for n, d in nx_graph.degree()]
    degree_counts = {}
    for d in degrees:
        degree_counts[d] = degree_counts.get(d, 0) + 1

    mean_degree = float(np.mean(degrees)) if degrees else 0.0

    # Clustering Coefficient (Average Local Clustering)
    clustering_coeffs = nx.clustering(nx_graph)
    avg_clustering = float(np.mean(list(clustering_coeffs.values()))) if clustering_coeffs else 0.0

    # Average Path Length (Handle Disconnected Graphs)
    is_connected = nx.is_connected(nx_graph) if num_nodes > 0 else False
    if is_connected:
        try:
            avg_path_length = float(nx.average_shortest_path_length(nx_graph))
        except Exception as e:
            logger.warning(f"Failed to compute average shortest path: {e}")
            avg_path_length = float('inf')
    else:
        # For disconnected graphs, we define average path length as infinity
        # as per the task requirement
        avg_path_length = float('inf')
        logger.info(f"Graph is disconnected. Setting average path length to infinity.")

    return {
        "degree_distribution": degree_counts,
        "mean_degree": mean_degree,
        "clustering_coefficient": avg_clustering,
        "average_path_length": avg_path_length,
        "num_nodes": num_nodes,
        "num_edges": num_edges,
        "is_connected": is_connected
    }