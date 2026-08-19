import networkx as nx
from typing import Dict, List, Tuple, Any, Optional, Union
from collections import deque

def is_dag(graph: nx.DiGraph) -> bool:
    """Check if a graph is a Directed Acyclic Graph."""
    return nx.is_directed_acyclic_graph(graph)

def validate_dag(graph: nx.DiGraph) -> bool:
    """Validate that the graph is a DAG and non-empty."""
    if not graph or not graph.nodes():
        return False
    return is_dag(graph)

def nesting_depth(graph: nx.DiGraph) -> int:
    """Calculate the longest path length (number of nodes) in the DAG."""
    if not graph.nodes():
        return 0
    try:
        return len(nx.dag_longest_path(graph))
    except nx.NetworkXUnfeasible:
        return 0

def longest_path(graph: nx.DiGraph) -> List[int]:
    """Return the list of nodes in the longest path."""
    if not graph.nodes():
        return []
    try:
        return nx.dag_longest_path(graph)
    except nx.NetworkXUnfeasible:
        return []

def branching_factor(graph: nx.DiGraph) -> float:
    """Calculate the mean in-degree of the graph."""
    if not graph.nodes():
        return 0.0
    in_degrees = [d for _, d in graph.in_degree()]
    if not in_degrees:
        return 0.0
    return sum(in_degrees) / len(in_degrees)

def compute_graph_metrics(graph: nx.DiGraph) -> Dict[str, Any]:
    """Compute a dictionary of graph metrics."""
    return {
        "is_dag": is_dag(graph),
        "nesting_depth": nesting_depth(graph),
        "branching_factor": branching_factor(graph),
        "longest_path": longest_path(graph),
        "num_nodes": graph.number_of_nodes(),
        "num_edges": graph.number_of_edges()
    }

def graph_from_dict(data: Dict[str, Any]) -> nx.DiGraph:
    """Reconstruct a DiGraph from a dictionary representation."""
    G = nx.DiGraph()
    if "nodes" in data:
        G.add_nodes_from(data["nodes"])
    if "edges" in data:
        G.add_edges_from(data["edges"])
    return G

def graph_to_dict(graph: nx.DiGraph) -> Dict[str, Any]:
    """Convert a DiGraph to a dictionary representation."""
    return {
        "nodes": list(graph.nodes()),
        "edges": list(graph.edges())
    }

def get_all_simple_paths_from_source_to_target(
    graph: nx.DiGraph,
    source: int,
    target: int
) -> List[List[int]]:
    """
    Find all simple paths from source to target in the graph.
    Returns a list of paths, where each path is a list of node IDs.
    """
    if source not in graph or target not in graph:
        return []
    try:
        return list(nx.all_simple_paths(graph, source=source, target=target))
    except nx.NetworkXError:
        return []

def get_random_valid_path_different_from_reference(
    graph: nx.DiGraph,
    reference_path: List[int],
    max_attempts: int = 1000
) -> Optional[List[int]]:
    """
    Select a valid ground-truth path that is different from the reference path.
    A valid path is defined as a simple path from a source node (in-degree 0) 
    to a sink node (out-degree 0).
    
    Args:
        graph: The DAG to search in.
        reference_path: The path to exclude (usually the longest path).
        max_attempts: Maximum number of random attempts to find a different path.
        
    Returns:
        A valid path list if found, None otherwise.
    """
    if not graph.nodes():
        return None
        
    # Identify sources and sinks
    sources = [n for n, d in graph.in_degree() if d == 0]
    sinks = [n for n, d in graph.out_degree() if d == 0]
    
    if not sources or not sinks:
        return None
        
    # If the reference path is the only path, we might not find another one
    # We try random sampling of source-sink pairs
    attempts = 0
    while attempts < max_attempts:
        src = sources[attempts % len(sources)]
        snk = sinks[attempts % len(sinks)]
        
        # Find all paths between this pair
        paths = list(nx.all_simple_paths(graph, source=src, target=snk))
        
        if not paths:
            attempts += 1
            continue
            
        # Pick a random path from this pair
        import random
        candidate = random.choice(paths)
        
        # Check if it's different from reference
        if candidate != reference_path:
            return candidate
            
        attempts += 1
        
    # If we exhausted attempts, try a more exhaustive search
    # (only if the graph is small enough to not hang)
    if graph.number_of_nodes() < 50:
        for src in sources:
            for snk in sinks:
                paths = list(nx.all_simple_paths(graph, source=src, target=snk))
                for p in paths:
                    if p != reference_path:
                        return p
    
    return None
