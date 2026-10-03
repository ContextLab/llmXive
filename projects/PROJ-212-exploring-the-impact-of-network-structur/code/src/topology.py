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
    - degree_distribution: Dictionary mapping degree to frequency count
    - mean_degree: Average degree of the graph
    - clustering_coefficient: Average clustering coefficient
    - average_path_length: Average shortest path length (infinity if disconnected)
    - is_connected: Boolean indicating if the graph is connected
    - num_nodes: Number of nodes
    - num_edges: Number of edges
    - density: Graph density

    Args:
        graph: A NetworkX Graph or NetworkGraph dataclass instance

    Returns:
        Dictionary containing all computed metrics
    """
    # Convert NetworkGraph dataclass to NetworkX Graph if necessary
    if isinstance(graph, NetworkGraph):
        # Assuming NetworkGraph has a 'graph' attribute that is a NetworkX Graph
        # or we reconstruct it from edges/node list
        if hasattr(graph, 'graph') and isinstance(graph.graph, nx.Graph):
            nx_graph = graph.graph
        elif hasattr(graph, 'edges') and hasattr(graph, 'nodes'):
            nx_graph = nx.Graph()
            nx_graph.add_nodes_from(graph.nodes)
            nx_graph.add_edges_from(graph.edges)
        else:
            raise ValueError("NetworkGraph instance does not contain valid graph data")
    elif isinstance(graph, nx.Graph):
        nx_graph = graph
    else:
        raise TypeError(f"Expected nx.Graph or NetworkGraph, got {type(graph)}")

    # Basic graph properties
    num_nodes = nx_graph.number_of_nodes()
    num_edges = nx_graph.number_of_edges()
    density = nx.density(nx_graph)
    is_connected = nx.is_connected(nx_graph)

    # Degree distribution
    degrees = [d for n, d in nx_graph.degree()]
    degree_counts = {}
    for d in degrees:
        degree_counts[d] = degree_counts.get(d, 0) + 1
    degree_distribution = dict(sorted(degree_counts.items()))

    # Mean degree
    mean_degree = np.mean(degrees) if degrees else 0.0

    # Clustering coefficient (average)
    clustering_coeff = nx.average_clustering(nx_graph) if num_nodes > 0 else 0.0

    # Average path length
    # Handle disconnected graphs: if not connected, average path length is infinity
    if is_connected:
        try:
            avg_path_length = nx.average_shortest_path_length(nx_graph)
        except nx.NetworkXError as e:
            logger.warning(f"Error computing average shortest path length: {e}")
            avg_path_length = float('inf')
    else:
        avg_path_length = float('inf')
        logger.info(f"Graph is disconnected. Average path length set to infinity.")

    metrics = {
        "num_nodes": num_nodes,
        "num_edges": num_edges,
        "density": density,
        "is_connected": is_connected,
        "mean_degree": float(mean_degree),
        "clustering_coefficient": float(clustering_coeff),
        "average_path_length": float(avg_path_length) if not np.isinf(avg_path_length) else float('inf'),
        "degree_distribution": degree_distribution
    }

    logger.info(f"Computed metrics for graph with {num_nodes} nodes and {num_edges} edges. "
                f"Connected: {is_connected}, Avg Path Length: {avg_path_length}")

    return metrics