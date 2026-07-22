"""
Graph utilities for building and manipulating memory graphs.
"""
import networkx as nx
import numpy as np
from typing import List, Dict, Tuple, Any, Optional, Set
import re
import logging

logger = logging.getLogger(__name__)

def build_memory_graph(context: str) -> nx.Graph:
    """
    Build a memory graph from a context string.
    
    Args:
        context: Context string containing entities and relationships.
    
    Returns:
        NetworkX graph representing the memory structure.
    """
    G = nx.Graph()
    
    # Simple entity extraction (split by sentences)
    sentences = re.split(r'[.!?]+', context)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    for i, sentence in enumerate(sentences):
        node_id = f"node_{i}"
        G.add_node(node_id, content=sentence, type="sentence")
        
        # Connect to previous sentence (simple chain)
        if i > 0:
            G.add_edge(f"node_{i-1}", node_id, type="sequential")
    
    # Add some semantic connections (placeholder for more advanced NLP)
    # In a real implementation, this would use entity recognition
    for i in range(len(sentences)):
        for j in range(i+1, len(sentences)):
            # Simple similarity check (very basic)
            if len(set(sentences[i].split()) & set(sentences[j].split())) > 2:
                G.add_edge(f"node_{i}", f"node_{j}", type="semantic", weight=0.5)
    
    logger.info(f"Built graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    return G

def inject_noise(graph: nx.Graph, noise_ratio: float = 0.1, seed: int = 42) -> nx.Graph:
    """
    Inject noise into a graph by replacing some edges with random distractor edges.
    
    Args:
        graph: Original graph.
        noise_ratio: Proportion of edges to replace.
        seed: Random seed for reproducibility.
    
    Returns:
        Noisy graph.
    """
    np.random.seed(seed)
    
    # Create a copy
    noisy_graph = graph.copy()
    
    # Get all edges
    edges = list(noisy_graph.edges())
    num_edges = len(edges)
    
    if num_edges == 0:
        logger.warning("Graph has no edges to inject noise into")
        return noisy_graph
    
    # Select edges to replace
    num_noise = int(num_edges * noise_ratio)
    noise_indices = np.random.choice(num_edges, size=min(num_noise, num_edges), replace=False)
    
    # Replace edges
    for idx in noise_indices:
        u, v = edges[idx]
        noisy_graph.remove_edge(u, v)
        
        # Add random edge between non-connected nodes
        nodes = list(noisy_graph.nodes())
        if len(nodes) > 1:
            while True:
                random_u = np.random.choice(nodes)
                random_v = np.random.choice(nodes)
                if random_u != random_v and not noisy_graph.has_edge(random_u, random_v):
                    noisy_graph.add_edge(random_u, random_v, type="noise")
                    break
    
    logger.info(f"Injected noise: replaced {num_noise} edges")
    return noisy_graph

def validate_graph(graph: nx.Graph) -> bool:
    """
    Validate a graph structure.
    
    Args:
        graph: Graph to validate.
    
    Returns:
        True if valid, False otherwise.
    """
    if graph.number_of_nodes() == 0:
        logger.warning("Graph has no nodes")
        return False
    
    if not nx.is_connected(graph):
        logger.warning("Graph is not connected")
        # This is a warning, not an error - we can still work with disconnected graphs
        return True
    
    return True

def get_graph_statistics(graph: nx.Graph) -> Dict[str, Any]:
    """
    Calculate statistics for a graph.
    
    Args:
        graph: Graph to analyze.
    
    Returns:
        Dictionary of statistics.
    """
    stats = {
        "num_nodes": graph.number_of_nodes(),
        "num_edges": graph.number_of_edges(),
        "density": nx.density(graph),
        "avg_degree": sum(dict(graph.degree()).values()) / graph.number_of_nodes() if graph.number_of_nodes() > 0 else 0,
        "is_connected": nx.is_connected(graph) if graph.number_of_nodes() > 0 else False,
        "num_components": nx.number_connected_components(graph)
    }
    
    return stats

def extract_subgraph_by_entities(graph: nx.Graph, entities: List[str]) -> nx.Graph:
    """
    Extract a subgraph containing only nodes related to specific entities.
    
    Args:
        graph: Original graph.
        entities: List of entity names to filter by.
    
    Returns:
        Subgraph containing relevant nodes.
    """
    relevant_nodes = set()
    
    for node_id, data in graph.nodes(data=True):
        content = data.get("content", "").lower()
        for entity in entities:
            if entity.lower() in content:
                relevant_nodes.add(node_id)
                break
    
    if not relevant_nodes:
        logger.warning("No relevant nodes found")
        return graph.subgraph([]).copy()
    
    subgraph = graph.subgraph(relevant_nodes).copy()
    logger.info(f"Extracted subgraph with {len(relevant_nodes)} nodes")
    return subgraph
