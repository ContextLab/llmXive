import networkx as nx
import random
from typing import Dict, List, Any, Optional

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
    """
    Calculate the mean in-degree of non-root nodes.
    Root nodes are those with in-degree 0.
    """
    if not graph.nodes():
        return 0.0
    
    # Only consider nodes that have at least one incoming edge
    non_roots = [d for n, d in graph.in_degree() if d > 0]
    
    if not non_roots:
        return 0.0
    
    return sum(non_roots) / len(non_roots)

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

def get_random_valid_path_different_from_reference(
    graph: nx.DiGraph,
    reference_path: List[int],
    max_attempts: int = 1000
) -> Optional[List[int]]:
    """
    Select a valid ground‑truth path that is different from the reference path.
    A valid path is defined as a simple path from a source node (in‑degree 0) 
    to a sink node (out‑degree 0).
    """
    if not graph.nodes():
        return None

    sources = [n for n, d in graph.in_degree() if d == 0]
    sinks = [n for n, d in graph.out_degree() if d == 0]

    if not sources or not sinks:
        return None

    attempts = 0
    while attempts < max_attempts:
        src = random.choice(sources)
        snk = random.choice(sinks)

        try:
            paths = list(nx.all_simple_paths(graph, source=src, target=snk))
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            attempts += 1
            continue

        if not paths:
            attempts += 1
            continue

        candidate = random.choice(paths)
        if candidate != reference_path:
            return candidate
        attempts += 1

    return None
