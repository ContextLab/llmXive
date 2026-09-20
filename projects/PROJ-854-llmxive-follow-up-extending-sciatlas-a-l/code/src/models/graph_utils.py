import networkx as nx
from typing import Dict, Any, Optional, List
import logging
from community import community_louvain

logger = logging.getLogger(__name__)

def louvain_cluster(G: nx.Graph) -> Dict[Any, int]:
    """
    T013: Run Louvain community detection on the graph G.
    Returns a dictionary mapping node -> cluster_id.
    """
    if G.number_of_nodes() == 0:
        return {}
    
    try:
        # community_louvain.best_partition returns {node: partition}
        partition = community_louvain.best_partition(G)
        return partition
    except Exception as e:
        logger.error(f"Louvain clustering failed: {e}")
        # Fallback: assign each node to its own cluster (0-based)
        return {node: i for i, node in enumerate(G.nodes())}

def calc_bridging(G: nx.Graph, clusters: Dict[Any, int]) -> None:
    """
    T014: Calculate bridging_coefficient for each node.
    Formula: (number of inter-cluster edges) / (total degree)
    Edge Case: Degree-0 nodes get 0.0.
    Updates G.nodes[node]['bridging_coefficient'] in place.
    """
    if G.number_of_nodes() == 0:
        return

    for node in G.nodes():
        degree = G.degree(node)
        if degree == 0:
            G.nodes[node]['bridging_coefficient'] = 0.0
            continue

        node_cluster = clusters.get(node)
        if node_cluster is None:
            # If no cluster assigned, treat as isolated or own cluster?
            # If no cluster, we can't calculate inter-cluster. Assume 0.
            G.nodes[node]['bridging_coefficient'] = 0.0
            continue

        inter_cluster_edges = 0
        for neighbor in G.neighbors(node):
            neighbor_cluster = clusters.get(neighbor)
            if neighbor_cluster is None:
                continue
            if neighbor_cluster != node_cluster:
                inter_cluster_edges += 1

        bridging = inter_cluster_edges / degree
        G.nodes[node]['bridging_coefficient'] = bridging

def validate_graph_structure(G: nx.Graph) -> bool:
    """
    Basic validation of graph structure.
    """
    if G.number_of_nodes() == 0:
        logger.warning("Graph is empty.")
        return False
    return True
