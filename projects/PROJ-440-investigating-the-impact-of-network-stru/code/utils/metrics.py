"""
Metrics computation utilities for network analysis.
"""
import networkx as nx
import numpy as np
from typing import Dict, Any, Tuple, Optional


def compute_clustering_coefficient(graph: nx.Graph) -> float:
    """
    Compute the global clustering coefficient of a graph.
    
    Args:
        graph: NetworkX graph
    
    Returns:
        Clustering coefficient (0 to 1)
    """
    return nx.clustering(graph)


def compute_average_path_length(graph: nx.Graph) -> float:
    """
    Compute the average shortest path length of a graph.
    
    Args:
        graph: NetworkX graph
    
    Returns:
        Average path length (float)
    """
    if nx.is_connected(graph):
        return nx.average_shortest_path_length(graph)
    else:
        # For disconnected graphs, compute average over connected components
        total_length = 0.0
        count = 0
        for component in nx.connected_components(graph):
            subgraph = graph.subgraph(component)
            if len(component) > 1:
                total_length += nx.average_shortest_path_length(subgraph)
                count += 1
        return total_length / count if count > 0 else float('inf')


def compute_degree_distribution_stats(graph: nx.Graph) -> Dict[str, Any]:
    """
    Compute statistics of the degree distribution.
    
    Args:
        graph: NetworkX graph
    
    Returns:
        Dictionary with degree distribution statistics
    """
    degrees = [d for n, d in graph.degree()]
    return {
        'mean': float(np.mean(degrees)),
        'std': float(np.std(degrees)),
        'min': int(np.min(degrees)),
        'max': int(np.max(degrees)),
        'median': float(np.median(degrees))
    }


def compute_graph_metrics(graph: nx.Graph) -> Dict[str, Any]:
    """
    Compute a comprehensive set of graph metrics.
    
    Args:
        graph: NetworkX graph
    
    Returns:
        Dictionary with all computed metrics
    """
    metrics = {
        'n_nodes': graph.number_of_nodes(),
        'n_edges': graph.number_of_edges(),
        'clustering_coefficient': float(nx.clustering(graph)),
        'average_path_length': compute_average_path_length(graph),
        'degree_stats': compute_degree_distribution_stats(graph),
        'avg_degree': float(np.mean([d for n, d in graph.degree()]))
    }
    
    return metrics
