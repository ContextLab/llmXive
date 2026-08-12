import networkx as nx
import numpy as np
from typing import List, Dict, Tuple, Any, Optional, Set
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def build_memory_graph(context: str) -> nx.DiGraph:
    """
    Constructs a directed graph from a context string.
    NOTE: This is a placeholder for T011a-1 logic which uses spaCy.
    For the purpose of this task (T011b), we assume the graph is already
    provided or constructed via the pipeline. This function is kept for API compatibility
    but T011b focuses on `inject_noise`.
    """
    G = nx.DiGraph()
    # Placeholder: In a real implementation, this would parse 'context' using spaCy
    # to extract (subject, relation, object) triples.
    # Since T011a-1 is the one responsible for this, and T011b depends on the output of T011a-1,
    # we assume the input 'graph' to inject_noise is already built.
    return G

def inject_noise(graph: nx.DiGraph, ratio: float, seed: int) -> nx.DiGraph:
    """
    Implements noise injection by replacing a proportion of existing edges with random edges.
    
    Parameters:
        graph (nx.DiGraph): The original memory graph.
        ratio (float): The proportion of edges to replace (e.g., 0.1 for 10%).
        seed (int): Random seed for reproducibility.
    
    Returns:
        nx.DiGraph: A new graph with injected noise.
    
    Algorithm:
        1. Set random seed.
        2. Identify all existing edges.
        3. Select `k = floor(ratio * total_edges)` edges to remove.
        4. Identify all possible non-adjacent node pairs (excluding self-loops).
        5. Select `k` random pairs from the non-adjacent set to add as new edges.
        6. Return the modified graph.
    """
    if ratio < 0 or ratio > 1:
        raise ValueError("Noise ratio must be between 0 and 1.")
    
    # Initialize random state for reproducibility
    rng = np.random.RandomState(seed)
    
    # Work on a copy to avoid modifying the original graph
    noisy_graph = graph.copy()
    
    total_edges = noisy_graph.number_of_edges()
    if total_edges == 0:
        logger.warning("Graph has no edges. Cannot inject noise.")
        return noisy_graph
    
    # Number of edges to replace
    num_to_replace = int(np.floor(ratio * total_edges))
    
    if num_to_replace == 0:
        logger.info(f"No edges to replace (ratio={ratio}, total={total_edges}).")
        return noisy_graph
    
    # 1. Select edges to remove
    all_edges = list(noisy_graph.edges())
    edges_to_remove = rng.choice(all_edges, size=num_to_replace, replace=False)
    
    # Remove selected edges
    for edge in edges_to_remove:
        noisy_graph.remove_edge(*edge)
    
    # 2. Identify potential new edges (non-adjacent pairs, no self-loops)
    nodes = list(noisy_graph.nodes())
    if len(nodes) < 2:
        logger.warning("Not enough nodes to generate new edges.")
        return noisy_graph
    
    current_edges_set = set(noisy_graph.edges())
    potential_new_edges = []
    
    for u in nodes:
        for v in nodes:
            if u == v:
                continue # No self-loops
            if (u, v) not in current_edges_set:
                potential_new_edges.append((u, v))
    
    if not potential_new_edges:
        logger.warning("No potential new edges available to add (fully connected or single node).")
        return noisy_graph
    
    # 3. Select edges to add
    num_to_add = min(num_to_replace, len(potential_new_edges))
    edges_to_add = rng.choice(potential_new_edges, size=num_to_add, replace=False)
    
    # Add selected edges
    for edge in edges_to_add:
        noisy_graph.add_edge(*edge)
    
    logger.info(f"Noise injection complete: removed {len(edges_to_remove)} edges, added {len(edges_to_add)} edges.")
    return noisy_graph

def validate_graph(graph: nx.DiGraph) -> Dict[str, Any]:
    """
    Validates the structure of a graph.
    Returns a dict with validation status and statistics.
    """
    stats = get_graph_statistics(graph)
    is_valid = True
    issues = []
    
    if not nx.is_directed(graph):
        issues.append("Graph is not directed.")
        is_valid = False
        
    if any(deg < 0 for _, deg in graph.in_degree()):
        issues.append("Invalid in-degree detected.")
        is_valid = False
        
    return {
        "is_valid": is_valid,
        "issues": issues,
        "statistics": stats
    }

def get_graph_statistics(graph: nx.DiGraph) -> Dict[str, Any]:
    """
    Computes basic statistics for a graph.
    """
    stats = {
        "num_nodes": graph.number_of_nodes(),
        "num_edges": graph.number_of_edges(),
        "density": nx.density(graph),
        "avg_in_degree": np.mean([d for _, d in graph.in_degree()]) if graph.number_of_nodes() > 0 else 0,
        "avg_out_degree": np.mean([d for _, d in graph.out_degree()]) if graph.number_of_nodes() > 0 else 0,
    }
    
    # Check for weakly connected components
    if graph.number_of_nodes() > 0:
        components = list(nx.weakly_connected_components(graph))
        stats["num_components"] = len(components)
        stats["largest_component_size"] = max(len(c) for c in components)
    else:
        stats["num_components"] = 0
        stats["largest_component_size"] = 0
        
    return stats

def extract_subgraph_by_entities(graph: nx.DiGraph, entities: List[str]) -> nx.DiGraph:
    """
    Extracts a subgraph containing only the specified entities and their connecting edges.
    """
    entity_set = set(entities)
    nodes_to_keep = set()
    
    # Find all nodes that are in the entity set or connected to them
    for node in graph.nodes():
        if node in entity_set:
            nodes_to_keep.add(node)
        else:
            # Check neighbors
            neighbors = set(graph.successors(node)) | set(graph.predecessors(node))
            if neighbors & entity_set:
                nodes_to_keep.add(node)
    
    return graph.subgraph(nodes_to_keep).copy()
