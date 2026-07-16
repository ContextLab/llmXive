"""
Graph utility functions for network topology analysis.

Provides connectivity checks and metric calculations for 
Watts-Strogatz small-world network analysis.
"""

import networkx as nx
from typing import Tuple, Optional, List
import numpy as np


def is_connected(graph: nx.Graph) -> bool:
    """
    Check if a NetworkX graph is connected.
    
    Args:
        graph: A NetworkX graph object.
        
    Returns:
        True if the graph is connected, False otherwise.
        
    Note:
        For directed graphs, this checks weak connectivity.
    """
    if graph.number_of_nodes() == 0:
        return False
    if graph.number_of_nodes() == 1:
        return True
    
    if graph.is_directed():
        return nx.is_weakly_connected(graph)
    else:
        return nx.is_connected(graph)


def calculate_clustering_coefficient(graph: nx.Graph) -> float:
    """
    Calculate the average clustering coefficient of a graph.
    
    Args:
        graph: A NetworkX graph object.
        
    Returns:
        The average clustering coefficient (float between 0 and 1).
    """
    if graph.number_of_nodes() == 0:
        return 0.0
    return nx.average_clustering(graph)


def calculate_average_path_length(graph: nx.Graph) -> float:
    """
    Calculate the average shortest path length of a connected graph.
    
    Args:
        graph: A NetworkX graph object.
        
    Returns:
        The average shortest path length, or float('inf') if disconnected.
        
    Raises:
        nx.NetworkXError: If the graph is not connected and not directed.
    """
    if not is_connected(graph):
        return float('inf')
    
    try:
        return nx.average_shortest_path_length(graph)
    except nx.NetworkXError:
        return float('inf')


def calculate_degree_distribution(graph: nx.Graph) -> Tuple[List[int], List[float]]:
    """
    Calculate the degree distribution of a graph.
    
    Args:
        graph: A NetworkX graph object.
        
    Returns:
        A tuple of (degrees, probabilities) where:
        - degrees: List of unique degree values
        - probabilities: Probability of each degree value
    """
    degrees = [d for _, d in graph.degree()]
    if not degrees:
        return [], []
    
    unique_degrees = sorted(set(degrees))
    counts = [degrees.count(k) for k in unique_degrees]
    total = len(degrees)
    probabilities = [c / total for c in counts]
    
    return unique_degrees, probabilities


def calculate_graph_metrics(graph: nx.Graph) -> dict:
    """
    Calculate a comprehensive set of graph metrics.
    
    Args:
        graph: A NetworkX graph object.
        
    Returns:
        A dictionary containing:
        - 'n_nodes': Number of nodes
        - 'n_edges': Number of edges
        - 'is_connected': Boolean connectivity status
        - 'avg_degree': Average node degree
        - 'clustering_coefficient': Average clustering coefficient
        - 'average_path_length': Average shortest path length (or inf if disconnected)
        - 'diameter': Graph diameter (or inf if disconnected)
        - 'density': Graph density
    """
    n_nodes = graph.number_of_nodes()
    n_edges = graph.number_of_edges()
    
    metrics = {
        'n_nodes': n_nodes,
        'n_edges': n_edges,
        'is_connected': is_connected(graph),
        'avg_degree': sum(d for _, d in graph.degree()) / n_nodes if n_nodes > 0 else 0.0,
        'clustering_coefficient': calculate_clustering_coefficient(graph),
        'density': nx.density(graph)
    }
    
    if is_connected(graph):
        try:
            metrics['average_path_length'] = calculate_average_path_length(graph)
            metrics['diameter'] = nx.diameter(graph)
        except nx.NetworkXError:
            metrics['average_path_length'] = float('inf')
            metrics['diameter'] = float('inf')
    else:
        metrics['average_path_length'] = float('inf')
        metrics['diameter'] = float('inf')
    
    return metrics


def validate_watts_strogatz_properties(
    graph: nx.Graph, 
    expected_n: int, 
    expected_k: int,
    tolerance: float = 0.01
) -> Tuple[bool, List[str]]:
    """
    Validate that a graph satisfies expected Watts-Strogatz properties.
    
    Args:
        graph: The graph to validate.
        expected_n: Expected number of nodes.
        expected_k: Expected average degree (each node connected to k neighbors).
        tolerance: Tolerance for average degree check.
        
    Returns:
        A tuple of (is_valid, list_of_violations).
    """
    violations = []
    
    # Check node count
    if graph.number_of_nodes() != expected_n:
        violations.append(f"Node count mismatch: got {graph.number_of_nodes()}, expected {expected_n}")
    
    # Check average degree
    avg_degree = sum(d for _, d in graph.degree()) / graph.number_of_nodes()
    if abs(avg_degree - expected_k) > tolerance:
        violations.append(f"Average degree mismatch: got {avg_degree:.4f}, expected {expected_k} (tolerance {tolerance})")
    
    # Check connectivity
    if not is_connected(graph):
        violations.append("Graph is not connected")
    
    return len(violations) == 0, violations