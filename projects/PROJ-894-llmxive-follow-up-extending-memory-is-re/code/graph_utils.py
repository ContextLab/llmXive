"""
Graph construction and noise injection utilities for LLM Agent Memory.

This module provides core functions to build memory graphs from structured
data, inject noise for robustness testing, and analyze graph properties.
"""

import networkx as nx
import numpy as np
from typing import List, Dict, Tuple, Any, Optional, Set
import re
import logging

# Configure logging for this module
logger = logging.getLogger(__name__)


def build_memory_graph(
    entities: List[Dict[str, Any]],
    relations: List[Dict[str, Any]]
) -> nx.DiGraph:
    """
    Construct a directed memory graph from lists of entities and relations.

    Args:
        entities: List of entity dicts. Expected keys: 'id', 'type', 'content'.
        relations: List of relation dicts. Expected keys: 'source_id', 'target_id', 'type', 'confidence'.

    Returns:
        A networkx DiGraph where nodes are entities and edges are relations.
    """
    G = nx.DiGraph()

    # Add nodes
    for ent in entities:
        node_id = ent.get('id')
        if not node_id:
            logger.warning("Entity missing 'id', skipping.")
            continue
        
        # Ensure node attributes are stored
        attrs = {k: v for k, v in ent.items() if k != 'id'}
        G.add_node(node_id, **attrs)

    # Add edges
    for rel in relations:
        src = rel.get('source_id')
        tgt = rel.get('target_id')
        
        if not src or not tgt:
            logger.warning("Relation missing source or target ID, skipping.")
            continue

        if not G.has_node(src) or not G.has_node(tgt):
            logger.warning(f"Relation references non-existent nodes {src} -> {tgt}, skipping.")
            continue

        attrs = {k: v for k, v in rel.items() if k not in ('source_id', 'target_id')}
        G.add_edge(src, tgt, **attrs)

    logger.info(f"Built graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    return G


def inject_noise(
    G: nx.DiGraph,
    noise_ratio: float = 0.1,
    seed: Optional[int] = None,
    noise_type: str = "random_edges"
) -> nx.DiGraph:
    """
    Inject noise into a memory graph to simulate retrieval errors or hallucinations.

    Supported noise types:
      - "random_edges": Adds random edges between unconnected nodes.
      - "distractor_edges": Adds edges from a specific 'distractor' source to random targets.
      - "remove_edges": Randomly removes existing edges.

    Args:
        G: The input graph (will be copied).
        noise_ratio: Ratio of noise relative to current graph size (edges or nodes).
        seed: Random seed for reproducibility.
        noise_type: Type of noise to inject.

    Returns:
        A new graph with noise injected.
    """
    if seed is not None:
        np.random.seed(seed)

    G_noisy = G.copy()
    nodes = list(G_noisy.nodes())
    n_nodes = len(nodes)

    if n_nodes == 0:
        logger.warning("Input graph is empty, cannot inject noise.")
        return G_noisy

    if noise_type == "random_edges":
        # Add random edges
        current_edges = set(G_noisy.edges())
        target_noise_count = int(n_nodes * noise_ratio)
        added = 0
        attempts = 0
        max_attempts = target_noise_count * 10

        while added < target_noise_count and attempts < max_attempts:
            u = np.random.choice(nodes)
            v = np.random.choice(nodes)
            if u != v and (u, v) not in current_edges:
                G_noisy.add_edge(u, v, type="noise", confidence=0.0, source="injected")
                current_edges.add((u, v))
                added += 1
            attempts += 1

        logger.info(f"Injected {added} random edges.")

    elif noise_type == "distractor_edges":
        # Identify a distractor node (or create one if none exists)
        # For simplicity, we pick a random existing node to act as the distractor source
        if n_nodes > 0:
            distractor = np.random.choice(nodes)
            target_noise_count = int(n_nodes * noise_ratio)
            targets = [n for n in nodes if n != distractor]
            
            if targets:
                selected_targets = np.random.choice(
                    targets, 
                    size=min(len(targets), target_noise_count), 
                    replace=False
                )
                for t in selected_targets:
                    G_noisy.add_edge(distractor, t, type="noise", confidence=0.0, source="distractor")
                logger.info(f"Injected edges from distractor '{distractor}' to {len(selected_targets)} targets.")

    elif noise_type == "remove_edges":
        # Remove random edges
        edges_to_remove = list(G_noisy.edges())
        if not edges_to_remove:
            logger.info("No edges to remove.")
            return G_noisy

        num_to_remove = int(len(edges_to_remove) * noise_ratio)
        num_to_remove = min(num_to_remove, len(edges_to_remove))
        
        selected = np.random.choice(len(edges_to_remove), size=num_to_remove, replace=False)
        for idx in selected:
            edge = edges_to_remove[idx]
            G_noisy.remove_edge(*edge)
        
        logger.info(f"Removed {num_to_remove} edges.")

    else:
        raise ValueError(f"Unknown noise_type: {noise_type}. Supported: random_edges, distractor_edges, remove_edges")

    return G_noisy


def validate_graph(G: nx.DiGraph) -> Dict[str, Any]:
    """
    Validate the integrity of a memory graph.

    Checks:
      - No self-loops (unless explicitly allowed by domain, here we flag them)
      - No isolated nodes (optional, but flagged)
      - Edge attribute consistency

    Returns:
        A dict with 'valid' (bool) and 'issues' (list of strings).
    """
    issues = []
    valid = True

    # Check for self-loops
    self_loops = list(nx.selfloop_edges(G))
    if self_loops:
        issues.append(f"Found {len(self_loops)} self-loops.")
        valid = False

    # Check for isolated nodes
    isolated = [n for n in G.nodes() if G.degree(n) == 0]
    if isolated:
        issues.append(f"Found {len(isolated)} isolated nodes.")
        # Not necessarily invalid, but worth noting

    # Check edge attributes consistency (optional strict check)
    # We assume if one edge has 'confidence', others should ideally too, 
    # but we won't mark it invalid unless critical.
    
    return {
        "valid": valid,
        "issues": issues,
        "node_count": G.number_of_nodes(),
        "edge_count": G.number_of_edges(),
        "is_connected": nx.is_weakly_connected(G) if G.number_of_nodes() > 0 else True
    }


def get_graph_statistics(G: nx.DiGraph) -> Dict[str, float]:
    """
    Compute basic statistics for a graph.

    Returns:
        Dict with density, avg_degree, clustering_coefficient (if undirected logic applied),
        and path lengths if applicable.
    """
    stats = {
        "num_nodes": G.number_of_nodes(),
        "num_edges": G.number_of_edges(),
        "density": nx.density(G)
    }

    if G.number_of_nodes() > 1:
        # Average degree
        degrees = [d for n, d in G.degree()]
        stats["avg_degree"] = np.mean(degrees)
        
        # Clustering coefficient (for directed graphs, uses average of in/out clustering or ignores direction)
        # nx.clustering on DiGraph treats it as undirected by default in some versions, 
        # or we can use transitivity.
        try:
            stats["transitivity"] = nx.transitivity(G)
        except ZeroDivisionError:
            stats["transitivity"] = 0.0

        # Average shortest path length (only if weakly connected component is large enough)
        # We use the largest weakly connected component for this
        try:
            if nx.is_weakly_connected(G):
                lengths = nx.shortest_path_length(G)
                # Filter out infinity if any (though connected implies finite)
                finite_lengths = [l for l in lengths.values() if l < np.inf]
                if finite_lengths:
                    stats["avg_path_length"] = np.mean([np.mean(v) for k, v in lengths.items()])
                else:
                    stats["avg_path_length"] = 0.0
            else:
                # Fallback: compute on largest component
                components = sorted(nx.weakly_connected_components(G), key=len, reverse=True)
                if components:
                    subG = G.subgraph(components[0])
                    lengths = nx.shortest_path_length(subG)
                    stats["avg_path_length_largest_component"] = np.mean([np.mean(v) for k, v in lengths.items()])
        except nx.NetworkXError:
            stats["avg_path_length"] = 0.0

    return stats


def extract_subgraph_by_entities(
    G: nx.DiGraph,
    entity_ids: Set[str],
    max_depth: int = 2
) -> nx.DiGraph:
    """
    Extract a subgraph centered around a set of entity IDs up to a certain depth.

    This is useful for retrieving relevant context for a specific query.

    Args:
        G: The full graph.
        entity_ids: Set of starting node IDs.
        max_depth: Maximum distance to traverse from starting nodes.

    Returns:
        A subgraph containing the starting nodes and their neighbors up to max_depth.
    """
    if not entity_ids:
        return G.subgraph([]).copy()

    # Identify nodes within max_depth
    nodes_to_keep = set()
    
    for start_node in entity_ids:
        if start_node not in G:
            logger.warning(f"Start node {start_node} not in graph.")
            continue
        
        # BFS to find neighbors within depth
        try:
            # nx.single_source_shortest_path_length returns {node: distance}
            paths = nx.single_source_shortest_path_length(G, start_node, cutoff=max_depth)
            nodes_to_keep.update(paths.keys())
        except nx.NetworkXError:
            continue

    return G.subgraph(nodes_to_keep).copy()