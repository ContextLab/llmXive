import networkx as nx
import logging
from typing import Dict, Any, List, Tuple, Optional, Union
from data_models import NetworkGraph
import numpy as np

logger = logging.getLogger(__name__)

def compute_metrics(graph: Union[nx.Graph, NetworkGraph]) -> Dict[str, Any]:
    """
    Compute topological metrics for a given NetworkX graph or NetworkGraph entity.
    
    Metrics computed:
    1. Degree Distribution: A dictionary mapping degree values to their frequencies.
    2. Clustering Coefficient: The average clustering coefficient of the graph.
    3. Average Path Length: The average shortest path length between all pairs of nodes.
       For disconnected graphs, this returns float('inf').
    
    Args:
        graph: A NetworkX graph instance or a NetworkGraph dataclass containing a graph.
    
    Returns:
        A dictionary containing the computed metrics.
    
    Raises:
        ValueError: If the graph is empty (no nodes).
        TypeError: If the input is not a valid graph type.
    """
    # Unwrap NetworkGraph if necessary
    if isinstance(graph, NetworkGraph):
        nx_graph = graph.graph
    elif isinstance(graph, nx.Graph):
        nx_graph = graph
    else:
        raise TypeError(f"Expected nx.Graph or NetworkGraph, got {type(graph)}")

    if nx_graph.number_of_nodes() == 0:
        raise ValueError("Cannot compute metrics for an empty graph.")

    metrics: Dict[str, Any] = {}

    # 1. Degree Distribution
    # NetworkX degree_histogram returns a list where index is degree and value is count.
    # We convert this to a dictionary for better readability and JSON serialization.
    degree_counts = dict(nx_graph.degree())
    degree_distribution: Dict[int, int] = {}
    for d in degree_counts.values():
        degree_distribution[d] = degree_distribution.get(d, 0) + 1
    # Sort by degree key for consistency
    metrics['degree_distribution'] = dict(sorted(degree_distribution.items()))

    # 2. Clustering Coefficient
    # Average clustering coefficient
    avg_clustering = nx.average_clustering(nx_graph)
    metrics['clustering_coefficient'] = float(avg_clustering)

    # 3. Average Path Length
    # Check connectivity
    if nx.is_connected(nx_graph):
        avg_path_length = nx.average_shortest_path_length(nx_graph)
        metrics['average_path_length'] = float(avg_path_length)
    else:
        # Handle disconnected graphs as infinity per spec
        logger.warning(f"Graph with {nx_graph.number_of_nodes()} nodes is disconnected. "
                     f"Setting average path length to infinity.")
        metrics['average_path_length'] = float('inf')
    
    # Additional metadata
    metrics['num_nodes'] = nx_graph.number_of_nodes()
    metrics['num_edges'] = nx_graph.number_of_edges()
    metrics['is_connected'] = nx.is_connected(nx_graph)
    metrics['density'] = nx.density(nx_graph)

    logger.info(f"Computed topology metrics for graph with {metrics['num_nodes']} nodes. "
               f"Clustering: {metrics['clustering_coefficient']:.4f}, "
               f"Path Length: {metrics['average_path_length']}")

    return metrics
