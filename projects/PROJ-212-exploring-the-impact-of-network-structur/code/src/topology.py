import networkx as nx
import logging
from typing import Dict, Any, List, Tuple, Optional, Union
from data_models import NetworkGraph

logger = logging.getLogger(__name__)

def compute_metrics(graph: Union[nx.Graph, NetworkGraph]) -> Dict[str, Any]:
    """
    Compute topological metrics for a given network graph.

    Calculates:
    - Degree distribution (mean, std, min, max)
    - Clustering coefficient (average)
    - Average path length (handling disconnected graphs as infinity)

    Args:
        graph: A NetworkX Graph object or a NetworkGraph dataclass containing
               an nx.Graph instance.

    Returns:
        A dictionary containing the computed metrics.
    """
    # Unwrap NetworkGraph if necessary
    if isinstance(graph, NetworkGraph):
        G = graph.graph
    else:
        G = graph

    if not isinstance(G, nx.Graph):
        raise TypeError(f"Expected networkx.Graph or NetworkGraph, got {type(G)}")

    if G.number_of_nodes() == 0:
        logger.warning("Graph is empty. Returning default metrics.")
        return {
            "degree_mean": 0.0,
            "degree_std": 0.0,
            "degree_min": 0,
            "degree_max": 0,
            "clustering_coefficient": 0.0,
            "average_path_length": float('inf'),
            "num_nodes": 0,
            "num_edges": 0,
            "is_connected": False
        }

    # Degree Distribution
    degrees = [d for n, d in G.degree()]
    degree_mean = float(nx.average_degree(G))
    degree_std = float(np.std(degrees)) if len(degrees) > 0 else 0.0
    degree_min = min(degrees) if degrees else 0
    degree_max = max(degrees) if degrees else 0

    # Clustering Coefficient
    clustering_coeff = float(nx.average_clustering(G))

    # Average Path Length (handling disconnected graphs)
    is_connected = nx.is_connected(G)
    if is_connected:
        avg_path_len = float(nx.average_shortest_path_length(G))
    else:
        # For disconnected graphs, average shortest path is undefined/infinite
        # We calculate the average over the largest connected component for reference,
        # but mark the global metric as infinity per spec.
        logger.warning("Graph is disconnected. Average path length set to infinity.")
        avg_path_len = float('inf')

        # Optional: Log stats for the largest component for debugging
        if nx.number_connected_components(G) > 0:
            largest_cc = max(nx.connected_components(G), key=len)
            subgraph = G.subgraph(largest_cc)
            if subgraph.number_of_nodes() > 1:
                try:
                    lcc_avg_path = float(nx.average_shortest_path_length(subgraph))
                    logger.info(f"Largest CC ({len(largest_cc)} nodes) avg path: {lcc_avg_path:.4f}")
                except Exception as e:
                    logger.warning(f"Could not compute path length for largest CC: {e}")

    return {
        "degree_mean": degree_mean,
        "degree_std": degree_std,
        "degree_min": degree_min,
        "degree_max": degree_max,
        "clustering_coefficient": clustering_coeff,
        "average_path_length": avg_path_len,
        "num_nodes": G.number_of_nodes(),
        "num_edges": G.number_of_edges(),
        "is_connected": is_connected,
        "num_components": nx.number_connected_components(G)
    }
