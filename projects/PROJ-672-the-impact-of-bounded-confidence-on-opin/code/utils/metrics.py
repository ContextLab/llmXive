"""
Structural metrics for NetworkX graphs.

This module provides functions to calculate key structural metrics for
network graphs used in the bounded confidence simulations.
"""
import networkx as nx
import numpy as np
from typing import Dict, Any, Optional


def calculate_assortativity(G: nx.Graph) -> float:
    """
    Calculate the degree assortativity coefficient of the graph.

    The assortativity coefficient measures the preference for nodes to attach
    to others with similar degree. Values range from -1 to 1.

    Args:
        G: A NetworkX graph.

    Returns:
        The assortativity coefficient as a float.
    """
    return nx.degree_assortativity_coefficient(G)


def calculate_average_path_length(G: nx.Graph) -> float:
    """
    Calculate the average shortest path length of the graph.

    For disconnected graphs, this calculates the average over all reachable
    pairs. If the graph is empty or has no edges, returns float('inf').

    Args:
        G: A NetworkX graph.

    Returns:
        The average shortest path length as a float.
    """
    if G.number_of_nodes() == 0:
        return float('inf')

    # Calculate shortest paths for all pairs
    try:
        # nx.average_shortest_path_length handles disconnected graphs by
        # raising an error if the graph is not connected, so we catch that
        # and compute manually for the largest connected component or
        # average over reachable pairs.
        return nx.average_shortest_path_length(G)
    except nx.NetworkXError:
        # Graph is disconnected, calculate average over largest connected component
        try:
            largest_cc = max(nx.connected_components(G), key=len)
            subgraph = G.subgraph(largest_cc)
            return nx.average_shortest_path_length(subgraph)
        except (ValueError, nx.NetworkXError):
            # Only isolated nodes or empty graph
            return float('inf')


def calculate_clustering_coefficient(G: nx.Graph) -> float:
    """
    Calculate the average clustering coefficient of the graph.

    The clustering coefficient measures the degree to which nodes in a graph
    tend to cluster together.

    Args:
        G: A NetworkX graph.

    Returns:
        The average clustering coefficient as a float.
    """
    return nx.average_clustering(G)


def calculate_structural_metrics(G: nx.Graph) -> Dict[str, Any]:
    """
    Calculate all structural metrics for a given graph.

    This function computes assortativity, average path length, and clustering
    coefficient in a single call.

    Args:
        G: A NetworkX graph.

    Returns:
        A dictionary containing the calculated metrics:
        - 'assortativity': float
        - 'average_path_length': float
        - 'clustering_coefficient': float
        - 'num_nodes': int
        - 'num_edges': int
    """
    return {
        'assortativity': calculate_assortativity(G),
        'average_path_length': calculate_average_path_length(G),
        'clustering_coefficient': calculate_clustering_coefficient(G),
        'num_nodes': G.number_of_nodes(),
        'num_edges': G.number_of_edges()
    }


def main():
    """
    Main function to demonstrate metric calculation.

    Creates a sample graph and prints its structural metrics.
    """
    # Create a sample Watts-Strogatz graph for demonstration
    G = nx.watts_strogatz_graph(n=100, k=4, p=0.1, seed=42)

    metrics = calculate_structural_metrics(G)

    print("Structural Metrics:")
    print(f"  Nodes: {metrics['num_nodes']}")
    print(f"  Edges: {metrics['num_edges']}")
    print(f"  Assortativity: {metrics['assortativity']:.4f}")
    print(f"  Average Path Length: {metrics['average_path_length']:.4f}")
    print(f"  Clustering Coefficient: {metrics['clustering_coefficient']:.4f}")


if __name__ == "__main__":
    main()