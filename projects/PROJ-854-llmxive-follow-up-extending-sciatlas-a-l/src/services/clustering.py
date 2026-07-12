import logging
from typing import Dict, List, Any

import networkx as nx
import community as community_louvain

from src.models.node import Node
from src.lib.config import RANDOM_SEED

logger = logging.getLogger(__name__)


def run_louvain_clustering(G: nx.Graph) -> Dict[int, List[int]]:
    """
    Run Louvain community detection on the input graph G.

    This function implements FR-002: Assign structural clusters using Louvain.
    It returns a mapping of cluster_id -> list of node_ids.

    Args:
        G (nx.Graph): The networkx graph containing nodes and edges.

    Returns:
        Dict[int, List[int]]: A dictionary where keys are cluster IDs (int)
            and values are lists of node IDs belonging to that cluster.
    """
    if G.number_of_nodes() == 0:
        logger.warning("Input graph has no nodes. Returning empty clusters.")
        return {}

    logger.info(f"Running Louvain clustering on graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")

    try:
        # community_louvain.partition returns {node: partition_id}
        # We set the random seed for reproducibility
        partition = community_louvain.best_partition(G, random_state=RANDOM_SEED)
    except Exception as e:
        logger.error(f"Louvain clustering failed: {e}")
        raise

    # Convert partition dict to cluster -> nodes list
    clusters: Dict[int, List[int]] = {}
    for node_id, cluster_id in partition.items():
        if cluster_id not in clusters:
            clusters[cluster_id] = []
        clusters[cluster_id].append(node_id)

    logger.info(f"Louvain clustering complete. Found {len(clusters)} communities.")
    return clusters


def assign_primary_clusters(G: nx.Graph, clusters: Dict[int, List[int]]) -> None:
    """
    Assign the 'primary_cluster' attribute to each node in the graph G
    based on the provided clusters mapping.

    This modifies G in-place.

    Args:
        G (nx.Graph): The networkx graph.
        clusters (Dict[int, List[int]]): Cluster mapping from run_louvain_clustering.
    """
    # Build reverse map: node_id -> cluster_id
    node_to_cluster: Dict[Any, int] = {}
    for cluster_id, node_list in clusters.items():
        for node_id in node_list:
            node_to_cluster[node_id] = cluster_id

    # Assign to graph nodes
    for node_id in G.nodes():
        if node_id in node_to_cluster:
            G.nodes[node_id]['primary_cluster'] = node_to_cluster[node_id]
        else:
            # Should not happen if clusters cover all nodes, but handle gracefully
            G.nodes[node_id]['primary_cluster'] = -1
            logger.warning(f"Node {node_id} not found in cluster mapping. Assigned to cluster -1.")

    logger.info(f"Assigned primary_cluster attribute to {len(node_to_cluster)} nodes.")