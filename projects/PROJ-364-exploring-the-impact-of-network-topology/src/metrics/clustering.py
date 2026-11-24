"""
Simple clustering coefficient calculations.
"""

import networkx as nx
from typing import Dict, Any

def calculate_clustering_coefficients(graph: nx.Graph) -> Dict[str, Any]:
    """
    Compute the global clustering coefficient for a graph.

    Returns a dictionary with:
        - clustering_coefficient (float): The average clustering coefficient.
    """
    if graph.number_of_nodes() == 0:
        coeff = 0.0
    else:
        coeff = nx.average_clustering(graph)
    return {"clustering_coefficient": float(coeff)}
