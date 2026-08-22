import networkx as nx
import numpy as np
from typing import Dict, Any, Tuple, Optional

def compute_clustering_coefficient(graph: nx.Graph) -> float:
    """
    Compute the average clustering coefficient of a graph.
    
    Args:
        graph: A NetworkX graph.
        
    Returns:
        float: The average clustering coefficient.
    """
    return nx.average_clustering(graph)

def compute_average_path_length(graph: nx.Graph) -> float:
    """
    Compute the average shortest path length of a graph.
    
    Args:
        graph: A NetworkX graph.
        
    Returns:
        float: The average shortest path length. Returns infinity if graph is disconnected.
    """
    if not nx.is_connected(graph):
        return float('inf')
    return nx.average_shortest_path_length(graph)

def compute_degree_distribution_stats(graph: nx.Graph) -> Dict[str, float]:
    """
    Compute statistics for the degree distribution of a graph.
    
    Args:
        graph: A NetworkX graph.
        
    Returns:
        dict: Dictionary containing mean, std, min, max, and median degree.
    """
    degrees = [d for n, d in graph.degree()]
    return {
        "mean": float(np.mean(degrees)),
        "std": float(np.std(degrees)),
        "min": float(np.min(degrees)),
        "max": float(np.max(degrees)),
        "median": float(np.median(degrees))
    }

def compute_graph_metrics(graph: nx.Graph) -> Dict[str, Any]:
    """
    Compute a comprehensive set of metrics for a graph.
    
    Args:
        graph: A NetworkX graph.
        
    Returns:
        dict: Dictionary containing various graph metrics.
    """
    metrics = {
        "clustering_coefficient": compute_clustering_coefficient(graph),
        "average_path_length": compute_average_path_length(graph),
        "num_nodes": graph.number_of_nodes(),
        "num_edges": graph.number_of_edges(),
        "degree_stats": compute_degree_distribution_stats(graph)
    }
    
    # Add density
    metrics["density"] = nx.density(graph)
    
    # Add diameter if connected
    if nx.is_connected(graph):
        metrics["diameter"] = nx.diameter(graph)
    else:
        metrics["diameter"] = float('inf')
        
    return metrics
