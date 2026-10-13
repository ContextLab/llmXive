"""
Structural metrics for NetworkX graphs.
This module provides functions to calculate key structural metrics for
network graphs used in the bounded confidence simulations.
"""
import networkx as nx
import numpy as np
from typing import Dict, Any

def calculate_assortativity(G: nx.Graph) -> float:
    """
    Calculate the degree assortativity coefficient of the graph.
    
    The assortativity coefficient measures the preference for nodes to attach
    to others with similar degree. Values range from -1 to 1.
    
    Special handling:
    * For regular graphs, NetworkX returns NaN because the degree variance is zero.
      In that case, we define the assortativity as 0.0.
    """
    coeff = nx.degree_assortativity_coefficient(G)
    if isinstance(coeff, float) and np.isnan(coeff):
        return 0.0
    return float(coeff)

def calculate_average_path_length(G: nx.Graph) -> float:
    """
    Calculate the average shortest path length of the graph.
    
    For disconnected graphs, this calculates the average over the largest 
    connected component. If the graph is empty or has no edges, returns float('inf').
    """
    if G.number_of_nodes() == 0:
        return float('inf')

    try:
        return nx.average_shortest_path_length(G)
    except nx.NetworkXError:
        try:
            largest_cc = max(nx.connected_components(G), key=len)
            subgraph = G.subgraph(largest_cc)
            return nx.average_shortest_path_length(subgraph)
        except (ValueError, nx.NetworkXError):
            return float('inf')

def calculate_clustering_coefficient(G: nx.Graph) -> float:
    """
    Calculate the average clustering coefficient of the graph.
    """
    return nx.average_clustering(G)

def calculate_structural_metrics(G: nx.Graph) -> Dict[str, Any]:
    """
    Calculate all structural metrics for a given graph.
    """
    return {
        'assortativity': calculate_assortativity(G),
        'average_path_length': calculate_average_path_length(G),
        'clustering_coefficient': calculate_clustering_coefficient(G),
        'num_nodes': G.number_of_nodes(),
        'num_edges': G.number_of_edges()
    }

def main():
    G = nx.watts_strogatz_graph(n=100, k=4, p=0.1, seed=42)
    metrics = calculate_structural_metrics(G)
    print(f"Metrics: {metrics}")

if __name__ == "__main__":
    main()
