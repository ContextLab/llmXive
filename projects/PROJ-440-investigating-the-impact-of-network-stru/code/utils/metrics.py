import networkx as nx
import numpy as np
from typing import Dict, Any, Tuple, Optional

def compute_clustering_coefficient(graph: nx.Graph) -> float:
    """Compute the average clustering coefficient of a graph."""
    return nx.average_clustering(graph)

def compute_average_path_length(graph: nx.Graph) -> float:
    """Compute the average shortest path length of a graph."""
    if not nx.is_connected(graph):
        # For disconnected graphs, compute average over largest component
        largest_cc = max(nx.connected_components(graph), key=len)
        subgraph = graph.subgraph(largest_cc)
        return nx.average_shortest_path_length(subgraph)
    return nx.average_shortest_path_length(graph)

def compute_degree_distribution_stats(graph: nx.Graph) -> Dict[str, float]:
    """Compute statistical properties of the degree distribution."""
    degrees = [d for n, d in graph.degree()]
    return {
        "mean": float(np.mean(degrees)),
        "std": float(np.std(degrees)),
        "min": float(np.min(degrees)),
        "max": float(np.max(degrees))
    }

def compute_graph_metrics(graph: nx.Graph) -> Dict[str, Any]:
    """Compute a comprehensive set of metrics for a graph."""
    return {
        "clustering_coefficient": compute_clustering_coefficient(graph),
        "average_path_length": compute_average_path_length(graph),
        "average_degree": sum(dict(graph.degree()).values()) / graph.number_of_nodes(),
        "degree_distribution_stats": compute_degree_distribution_stats(graph)
    }
