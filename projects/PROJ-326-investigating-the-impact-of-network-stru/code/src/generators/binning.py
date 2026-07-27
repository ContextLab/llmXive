"""
Binning logic for clustering coefficients.
"""

import logging
from typing import List, Optional, Tuple
import networkx as nx

logger = logging.getLogger(__name__)


def get_clustering_coefficient(graph: nx.Graph) -> float:
    """
    Calculate the global clustering coefficient of a graph.
    """
    if graph.number_of_nodes() < 3:
        return 0.0
    return nx.transitivity(graph)


def classify_graph(graph: nx.Graph, bins: Optional[List[float]] = None) -> str:
    """
    Classify a graph into a bin based on its clustering coefficient.
    
    Args:
        graph: The graph to classify.
        bins: List of bin thresholds (e.g., [0.1, 0.2, 0.3]).
    
    Returns:
        String identifier for the bin (e.g., "0.2").
    """
    if bins is None:
        bins = [0.1, 0.2, 0.3, 0.4, 0.5]
    
    cc = get_clustering_coefficient(graph)
    
    for i, threshold in enumerate(bins):
        if cc < threshold:
            return str(threshold)
    
    # If larger than all bins, return the last bin or a special tag
    return str(bins[-1])
