import logging
from typing import Any, Dict, List, Optional
import networkx as nx

logger = logging.getLogger(__name__)


def compute_graph_metrics(graph: Any) -> Dict[str, Any]:
    """
    Compute topological metrics for a given graph.
    Returns a dictionary containing:
    - degree_distribution
    - clustering_coefficient
    - average_path_length
    - number_of_nodes
    - number_of_edges
    - is_connected
    """
    if not isinstance(graph, nx.Graph):
        raise TypeError("Input must be a NetworkX graph.")

    metrics = {
        "number_of_nodes": graph.number_of_nodes(),
        "number_of_edges": graph.number_of_edges(),
        "is_connected": nx.is_connected(graph),
        "clustering_coefficient": nx.average_clustering(graph),
        "average_path_length": 0.0
    }

    if nx.is_connected(graph):
        metrics["average_path_length"] = nx.average_path_length(graph)
    else:
        # For disconnected graphs, average path length is undefined or infinity
        # We'll set it to -1 to indicate undefined
        metrics["average_path_length"] = -1.0

    # Degree distribution
    degrees = [d for n, d in graph.degree()]
    metrics["degree_distribution"] = {
        "mean": float(sum(degrees) / len(degrees)) if degrees else 0.0,
        "max": float(max(degrees)) if degrees else 0.0,
        "min": float(min(degrees)) if degrees else 0.0
    }

    logger.debug(f"Computed metrics for graph with {metrics['number_of_nodes']} nodes")
    return metrics
