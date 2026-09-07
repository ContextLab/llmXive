import networkx as nx
import logging
from typing import Dict, Any, List, Tuple, Optional, Union
from data_models import NetworkGraph
import numpy as np

logger = logging.getLogger(__name__)

def compute_metrics(graph: Union[nx.Graph, NetworkGraph]) -> Dict[str, Any]:
    """
    Compute topological metrics for a given network graph.

    Metrics computed:
    - degree_distribution: List of degrees for all nodes
    - mean_degree: Average degree of the graph
    - clustering_coefficient: Global clustering coefficient (transitivity)
    - average_clustering: Average local clustering coefficient
    - average_path_length: Average shortest path length (infinity if disconnected)
    - number_of_nodes: Total number of nodes
    - number_of_edges: Total number of edges
    - is_connected: Boolean indicating if the graph is connected

    Args:
        graph: A NetworkX graph or NetworkGraph object containing a NetworkX graph.

    Returns:
        A dictionary containing the computed metrics.
    """
    # Extract the NetworkX graph if a NetworkGraph object is passed
    if isinstance(graph, NetworkGraph):
        nx_graph = graph.graph
    else:
        nx_graph = graph

    # Validate input
    if not isinstance(nx_graph, nx.Graph):
        raise TypeError("Input must be a networkx.Graph or a NetworkGraph with a graph attribute")

    if nx_graph.number_of_nodes() == 0:
        logger.warning("Graph is empty. Returning default metrics with zeros/infinity.")
        return {
            "degree_distribution": [],
            "mean_degree": 0.0,
            "clustering_coefficient": 0.0,
            "average_clustering": 0.0,
            "average_path_length": float('inf'),
            "number_of_nodes": 0,
            "number_of_edges": 0,
            "is_connected": False
        }

    # Check connectivity
    is_connected = nx.is_connected(nx_graph)

    # Degree distribution
    degrees = [d for n, d in nx_graph.degree()]
    degree_distribution = degrees

    # Mean degree
    mean_degree = np.mean(degrees) if degrees else 0.0

    # Global clustering coefficient (transitivity)
    clustering_coefficient = nx.transitivity(nx_graph)

    # Average clustering coefficient
    average_clustering = nx.average_clustering(nx_graph)

    # Average path length
    # Handle disconnected graphs: return infinity
    if is_connected:
        try:
            average_path_length = nx.average_shortest_path_length(nx_graph)
        except nx.NetworkXError as e:
            logger.error(f"Error computing average shortest path length: {e}")
            average_path_length = float('inf')
    else:
        logger.warning("Graph is disconnected. Setting average path length to infinity.")
        average_path_length = float('inf')

    metrics = {
        "degree_distribution": degree_distribution,
        "mean_degree": float(mean_degree),
        "clustering_coefficient": float(clustering_coefficient),
        "average_clustering": float(average_clustering),
        "average_path_length": float(average_path_length),
        "number_of_nodes": nx_graph.number_of_nodes(),
        "number_of_edges": nx_graph.number_of_edges(),
        "is_connected": is_connected
    }

    logger.info(f"Computed topology metrics for graph with {metrics['number_of_nodes']} nodes.")
    return metrics
