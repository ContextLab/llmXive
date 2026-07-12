import networkx as nx
from typing import Dict, Any, Optional, List
import logging
from community import community_louvain

logger = logging.getLogger(__name__)

def louvain_cluster(G: nx.Graph, resolution: float = 1.0) -> Dict[str, int]:
    """
    Run Louvain community detection on graph G.
    
    Args:
        G: networkx.Graph
        resolution: Resolution parameter for Louvain
    
    Returns:
        Dictionary mapping node_id (str) to cluster_id (int)
    """
    if G.number_of_nodes() == 0:
        return {}
    
    try:
        partition = community_louvain.best_partition(G, resolution=resolution)
        return partition
    except Exception as e:
        logger.error(f"Louvain clustering failed: {e}")
        return {}

def calc_bridging(G: nx.Graph, clusters: Dict[str, int]) -> Dict[str, float]:
    """
    Calculate bridging coefficient for each node.
    Bridging = (number of edges to nodes in other clusters) / (total degree)
    
    Args:
        G: networkx.Graph
        clusters: Dict mapping node_id to cluster_id
    
    Returns:
        Dict mapping node_id to bridging_coefficient (0.0 to 1.0)
    """
    bridging_coeffs = {}
    
    for node in G.nodes():
        node_str = str(node)
        degree = G.degree(node)
        
        if degree == 0:
            bridging_coeffs[node_str] = 0.0
            continue
        
        # Count edges to other clusters
        inter_cluster_edges = 0
        node_cluster = clusters.get(node_str)
        
        for neighbor in G.neighbors(node):
            neighbor_str = str(neighbor)
            neighbor_cluster = clusters.get(neighbor_str)
            
            # If neighbor has no cluster assigned, treat as different cluster?
            # Or skip? Spec says "inter-cluster edges".
            # If node_cluster is None or neighbor_cluster is None, we might count it.
            # Let's assume if cluster is missing, it's a different cluster.
            if node_cluster != neighbor_cluster:
                inter_cluster_edges += 1
        
        coeff = inter_cluster_edges / degree
        bridging_coeffs[node_str] = coeff
    
    return bridging_coeffs

def validate_graph_structure(G: nx.Graph) -> bool:
    """
    Validate that the graph has the expected structure and attributes.
    """
    if G.number_of_nodes() == 0:
        logger.warning("Graph is empty.")
        return False
    
    # Check for required attributes if needed
    return True
