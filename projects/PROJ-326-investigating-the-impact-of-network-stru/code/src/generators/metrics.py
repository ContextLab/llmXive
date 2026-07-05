"""
Metric extraction functions for network topologies.

This module provides functions to compute key topological metrics
from generated graphs: degree distribution, clustering coefficients,
and average path length.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple

import networkx as nx
import numpy as np

logger = logging.getLogger(__name__)


def compute_degree_distribution(G: nx.Graph) -> Dict[int, int]:
    """
    Compute the degree distribution of a graph.

    Args:
        G: A NetworkX graph.

    Returns:
        A dictionary mapping degree value to count of nodes with that degree.
    """
    if G.number_of_nodes() == 0:
        return {}

    degrees = [d for _, d in G.degree()]
    distribution: Dict[int, int] = {}
    for d in degrees:
        distribution[d] = distribution.get(d, 0) + 1

    return distribution


def compute_degree_statistics(G: nx.Graph) -> Dict[str, float]:
    """
    Compute summary statistics for the degree distribution.

    Args:
        G: A NetworkX graph.

    Returns:
        Dictionary with mean, std, min, max, and median degree.
    """
    if G.number_of_nodes() == 0:
        return {
            "mean_degree": 0.0,
            "std_degree": 0.0,
            "min_degree": 0.0,
            "max_degree": 0.0,
            "median_degree": 0.0
        }

    degrees = np.array([d for _, d in G.degree()])
    return {
        "mean_degree": float(np.mean(degrees)),
        "std_degree": float(np.std(degrees)),
        "min_degree": float(np.min(degrees)),
        "max_degree": float(np.max(degrees)),
        "median_degree": float(np.median(degrees))
    }


def compute_clustering_coefficients(G: nx.Graph) -> Dict[str, float]:
    """
    Compute clustering coefficient metrics.

    Args:
        G: A NetworkX graph.

    Returns:
        Dictionary containing:
            - global_clustering: The average clustering coefficient.
            - max_clustering: The maximum local clustering coefficient.
            - min_clustering: The minimum local clustering coefficient.
    """
    if G.number_of_nodes() == 0:
        return {
            "global_clustering": 0.0,
            "max_clustering": 0.0,
            "min_clustering": 0.0
        }

    local_clustering = nx.clustering(G)
    values = list(local_clustering.values())

    return {
        "global_clustering": float(nx.average_clustering(G)),
        "max_clustering": float(max(values)) if values else 0.0,
        "min_clustering": float(min(values)) if values else 0.0
    }


def compute_average_path_length(G: nx.Graph) -> float:
    """
    Compute the average shortest path length.

    For disconnected graphs, this computes the average over all connected
    components. If the graph has no edges or only one node, returns infinity.

    Args:
        G: A NetworkX graph.

    Returns:
        The average shortest path length. Returns float('inf') if undefined.
    """
    if G.number_of_nodes() <= 1:
        return float('inf')

    try:
        # average_shortest_path_length handles disconnected graphs by averaging
        # over all pairs in the same component
        return float(nx.average_shortest_path_length(G))
    except nx.NetworkXError:
        # This can happen if the graph is disconnected and we can't compute
        # paths between all pairs. Fallback to component-wise average.
        logger.warning("Graph is disconnected; computing component-wise average path length.")
        components = nx.connected_components(G)
        total_length = 0.0
        total_pairs = 0

        for component in components:
            subgraph = G.subgraph(component)
            if len(component) > 1:
                try:
                    length = nx.average_shortest_path_length(subgraph)
                    total_length += length * (len(component) * (len(component) - 1))
                    total_pairs += len(component) * (len(component) - 1)
                except nx.NetworkXError:
                    continue

        if total_pairs == 0:
            return float('inf')
        return float(total_length / total_pairs)


def extract_all_metrics(G: nx.Graph, graph_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract all topological metrics for a given graph.

    This function aggregates degree distribution, degree statistics,
    clustering coefficients, and average path length into a single
    metrics dictionary suitable for logging or analysis.

    Args:
        G: A NetworkX graph.
        graph_id: Optional identifier for the graph (e.g., from metadata).

    Returns:
        A dictionary containing:
            - graph_id: The provided ID or None.
            - num_nodes: Number of nodes in the graph.
            - num_edges: Number of edges in the graph.
            - is_connected: Boolean indicating if the graph is connected.
            - degree_distribution: Dict of degree -> count.
            - degree_statistics: Dict of degree summary stats.
            - clustering_coefficients: Dict of clustering stats.
            - average_path_length: The average shortest path length.
    """
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()
    is_connected = nx.is_connected(G) if num_nodes > 0 else False

    return {
        "graph_id": graph_id,
        "num_nodes": num_nodes,
        "num_edges": num_edges,
        "is_connected": is_connected,
        "degree_distribution": compute_degree_distribution(G),
        "degree_statistics": compute_degree_statistics(G),
        "clustering_coefficients": compute_clustering_coefficients(G),
        "average_path_length": compute_average_path_length(G)
    }


def validate_metrics(metrics: Dict[str, Any], required_keys: Optional[List[str]] = None) -> Tuple[bool, List[str]]:
    """
    Validate that a metrics dictionary contains required keys and valid values.

    Args:
        metrics: The metrics dictionary to validate.
        required_keys: Optional list of keys that must be present. Defaults to
                       ['num_nodes', 'num_edges', 'is_connected', 'degree_statistics',
                        'clustering_coefficients', 'average_path_length'].

    Returns:
        A tuple (is_valid, missing_or_invalid_keys).
    """
    default_required = [
        'num_nodes', 'num_edges', 'is_connected',
        'degree_statistics', 'clustering_coefficients', 'average_path_length'
    ]
    keys_to_check = required_keys if required_keys is not None else default_required

    missing_keys = []
    for key in keys_to_check:
        if key not in metrics:
            missing_keys.append(key)
            continue

        # Validate specific value constraints
        if key == 'num_nodes' and metrics[key] < 0:
            missing_keys.append(f"{key} (negative value)")
        elif key == 'num_edges' and metrics[key] < 0:
            missing_keys.append(f"{key} (negative value)")
        elif key == 'is_connected' and not isinstance(metrics[key], bool):
            missing_keys.append(f"{key} (not boolean)")
        elif key == 'average_path_length' and metrics[key] is None:
            missing_keys.append(f"{key} (None value)")

    return len(missing_keys) == 0, missing_keys