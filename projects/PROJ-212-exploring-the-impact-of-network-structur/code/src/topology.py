import networkx as nx
import logging
from typing import Dict, Any, List, Tuple, Optional, Union
from data_models import NetworkGraph
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def compute_metrics(graph: nx.Graph) -> Dict[str, Any]:
    """
    Computes topological metrics for a given network graph.
    Metrics: degree distribution, clustering coefficient, average path length.
    """
    if graph.number_of_nodes() == 0:
        logger.warning("Empty graph provided.")
        return {
            "degree_distribution": [],
            "mean_degree": 0.0,
            "clustering_coefficient": 0.0,
            "average_path_length": float('inf'),
            "is_connected": False
        }

    # Degree distribution
    degrees = [d for n, d in graph.degree()]
    degree_distribution = sorted(degrees)
    mean_degree = np.mean(degrees) if degrees else 0.0

    # Clustering coefficient
    clustering_coeff = nx.average_clustering(graph)

    # Average path length
    # Handle disconnected graphs
    if nx.is_connected(graph):
        avg_path_length = nx.average_shortest_path_length(graph)
    else:
        # For disconnected graphs, average path length is undefined/infinite
        # We'll compute it for the largest connected component or return infinity
        try:
            largest_cc = max(nx.connected_components(graph), key=len)
            subgraph = graph.subgraph(largest_cc)
            avg_path_length = nx.average_shortest_path_length(subgraph)
            # Or we can return infinity for the whole graph
            # Let's return infinity to be consistent with the spec
            avg_path_length = float('inf')
        except:
            avg_path_length = float('inf')

    return {
        "degree_distribution": degree_distribution,
        "mean_degree": float(mean_degree),
        "clustering_coefficient": float(clustering_coeff),
        "average_path_length": float(avg_path_length),
        "is_connected": nx.is_connected(graph)
    }
