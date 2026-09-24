import networkx as nx
from typing import Dict, Any, Optional, List
import logging
from community import community_louvain

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def louvain_cluster(G: nx.Graph) -> Dict[Any, int]:
    """
    Run Louvain community detection on the graph G.
    Returns a dictionary mapping node_id to cluster_id.
    """
    if G.number_of_nodes() == 0:
        return {}
    
    # Run Louvain
    try:
        partition = community_louvain.best_partition(G)
        return partition
    except Exception as e:
        logger.error(f"Louvain clustering failed: {e}")
        # Fallback: assign all to cluster 0
        return {node: 0 for node in G.nodes()}

def calc_bridging(G: nx.Graph, clusters: Dict[Any, int]) -> Dict[Any, float]:
    """
    Calculate bridging coefficient for each node.
    Bridging coefficient = (number of inter-cluster edges) / (total degree)
    Handles degree-0 nodes by assigning 0.0.
    """
    bridging_coeffs = {}
    
    for node in G.nodes():
        degree = G.degree(node)
        if degree == 0:
            bridging_coeffs[node] = 0.0
            continue
        
        node_cluster = clusters.get(node)
        inter_cluster_edges = 0
        
        for neighbor in G.neighbors(node):
            neighbor_cluster = clusters.get(neighbor)
            if node_cluster != neighbor_cluster:
                inter_cluster_edges += 1
        
        bridging_coeffs[node] = inter_cluster_edges / degree
    
    return bridging_coeffs

def validate_graph_structure(G: nx.Graph) -> bool:
    """
    Validate that the graph has the necessary structure for analysis.
    """
    if G.number_of_nodes() == 0:
        logger.warning("Graph is empty.")
        return False
    return True
