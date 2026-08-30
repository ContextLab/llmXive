import networkx as nx
import numpy as np
from typing import List, Dict, Tuple, Any, Optional, Set
import re
import logging

logger = logging.getLogger(__name__)

def build_memory_graph(triples: List[Tuple[str, str, str]]) -> nx.DiGraph:
    """
    Build a directed memory graph from a list of (subject, verb, object) triples.
    
    Args:
        triples: List of tuples (subject, predicate, object)
    
    Returns:
        networkx.DiGraph: The constructed memory graph
    """
    G = nx.DiGraph()
    
    for s, p, o in triples:
        # Add nodes if they don't exist
        if not G.has_node(s):
            G.add_node(s)
        if not G.has_node(o):
            G.add_node(o)
        
        # Add edge with predicate as attribute
        G.add_edge(s, o, predicate=p)
    
    return G

def inject_noise(graph: nx.DiGraph, density: float, seed: int) -> nx.DiGraph:
    """
    Inject noise into a graph by adding random edges.
    
    This function implements the "Edge Addition" logic as mandated by the spec:
    It adds random edges to the existing set at a fixed density relative to the
    original edge count, ensuring the total edge count increases.
    
    Args:
        graph: The original clean graph (nx.DiGraph)
        density: The density of noise to add (e.g., 0.1 means add 10% of original edge count)
        seed: Random seed for reproducibility
    
    Returns:
        nx.DiGraph: A new graph with injected noise (original graph is not modified)
    
    Raises:
        ValueError: If density is negative or seed is invalid
    """
    if density < 0:
        raise ValueError(f"Density must be non-negative, got {density}")
    
    # Set seed for reproducibility
    np.random.seed(seed)
    
    # Create a copy of the graph to avoid modifying the original
    noisy_graph = graph.copy()
    
    # Calculate the number of edges to add based on density
    original_edge_count = graph.number_of_edges()
    edges_to_add = max(1, int(original_edge_count * density))
    
    # Get all nodes
    nodes = list(noisy_graph.nodes())
    n_nodes = len(nodes)
    
    if n_nodes < 2:
        logger.warning("Graph has fewer than 2 nodes, cannot add edges.")
        return noisy_graph
    
    # Generate candidate edges that don't already exist
    existing_edges = set(noisy_graph.edges())
    candidates = []
    
    for u in nodes:
        for v in nodes:
            if u != v and (u, v) not in existing_edges:
                candidates.append((u, v))
    
    if not candidates:
        logger.warning("No candidate edges available to add. Graph is fully connected.")
        return noisy_graph
    
    # Randomly select edges to add
    num_to_add = min(edges_to_add, len(candidates))
    selected_edges = np.random.choice(len(candidates), size=num_to_add, replace=False)
    
    for idx in selected_edges:
        u, v = candidates[idx]
        noisy_graph.add_edge(u, v, predicate="NOISE_ADDED")
    
    logger.info(f"Injected {num_to_add} noise edges into graph. "
               f"Original edges: {original_edge_count}, New total: {noisy_graph.number_of_edges()}")
    
    return noisy_graph

def validate_graph(graph: nx.DiGraph) -> Tuple[bool, List[str]]:
    """
    Validate a graph structure and return validation status and issues.
    
    Args:
        graph: The graph to validate
    
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    if graph.number_of_nodes() == 0:
        issues.append("Graph has no nodes")
    
    if graph.number_of_edges() == 0 and graph.number_of_nodes() > 1:
        issues.append("Graph has nodes but no edges (disconnected)")
    
    # Check for self-loops (optional, depending on requirements)
    self_loops = [e for e in graph.edges() if e[0] == e[1]]
    if self_loops:
        issues.append(f"Graph contains {len(self_loops)} self-loops")
    
    is_valid = len(issues) == 0
    return is_valid, issues

def get_graph_statistics(graph: nx.DiGraph) -> Dict[str, Any]:
    """
    Calculate and return basic statistics about the graph.
    
    Args:
        graph: The graph to analyze
    
    Returns:
        Dictionary containing graph statistics
    """
    stats = {
        "num_nodes": graph.number_of_nodes(),
        "num_edges": graph.number_of_edges(),
        "is_connected": nx.is_strongly_connected(graph) if graph.number_of_nodes() > 0 else False,
        "num_components": nx.number_strongly_connected_components(graph) if graph.number_of_nodes() > 0 else 0,
        "avg_degree": graph.number_of_edges() * 2 / graph.number_of_nodes() if graph.number_of_nodes() > 0 else 0,
        "density": nx.density(graph),
    }
    
    # Calculate connected components if not fully connected
    if not stats["is_connected"]:
        components = list(nx.strongly_connected_components(graph))
        stats["largest_component_size"] = max(len(c) for c in components) if components else 0
        stats["num_components"] = len(components)
    
    return stats

def extract_subgraph_by_entities(graph: nx.DiGraph, entities: Set[str]) -> nx.DiGraph:
    """
    Extract a subgraph containing only the specified entities and edges between them.
    
    Args:
        graph: The original graph
        entities: Set of entity names to include in the subgraph
    
    Returns:
        nx.DiGraph: The extracted subgraph
    """
    # Filter nodes that are in the entities set
    valid_nodes = [n for n in graph.nodes() if n in entities]
    
    if not valid_nodes:
        return nx.DiGraph()
    
    # Create subgraph
    subgraph = graph.subgraph(valid_nodes).copy()
    
    logger.debug(f"Extracted subgraph with {subgraph.number_of_nodes()} nodes "
                f"and {subgraph.number_of_edges()} edges from {len(entities)} requested entities")
    
    return subgraph

def detect_degenerate_graph(graph: nx.DiGraph) -> Tuple[bool, List[str]]:
    """
    Detect degenerate graph conditions: disconnected components and single-node graphs.
    
    This function explicitly checks for:
    1. Single-node graphs (only one node, no edges)
    2. Disconnected graphs (multiple strongly connected components)
    3. Empty graphs (no nodes)
    
    Args:
        graph: The graph to check for degeneracy
    
    Returns:
        Tuple of (is_degenerate, list_of_degeneracy_reasons)
    """
    degeneracy_reasons = []
    
    num_nodes = graph.number_of_nodes()
    num_edges = graph.number_of_edges()
    
    # Check for empty graph
    if num_nodes == 0:
        degeneracy_reasons.append("EMPTY_GRAPH: No nodes in the graph")
        return True, degeneracy_reasons
    
    # Check for single-node graph
    if num_nodes == 1:
        degeneracy_reasons.append("SINGLE_NODE: Graph contains only one node")
        # A single node with no edges is degenerate
        if num_edges == 0:
            degeneracy_reasons.append("NO_EDGES: Single node has no edges")
        return True, degeneracy_reasons
    
    # Check for disconnected components
    try:
        num_components = nx.number_strongly_connected_components(graph)
        if num_components > 1:
            degeneracy_reasons.append(f"DISCONNECTED: Graph has {num_components} strongly connected components")
            
            # Log sizes of components for debugging
            components = list(nx.strongly_connected_components(graph))
            component_sizes = [len(c) for c in components]
            logger.debug(f"Component sizes: {component_sizes}")
            
            return True, degeneracy_reasons
    except nx.NetworkXError as e:
        logger.warning(f"Error checking connectivity: {e}")
        degeneracy_reasons.append(f"CONNECTIVITY_CHECK_ERROR: {str(e)}")
        return True, degeneracy_reasons
    
    return False, degeneracy_reasons

def handle_degenerate_graph(graph: nx.DiGraph, strategy_name: str) -> Tuple[nx.DiGraph, Dict[str, Any]]:
    """
    Handle degenerate graphs by applying appropriate fallback logic.
    
    For degenerate graphs:
    - Empty graphs: Return an empty graph with metadata
    - Single-node graphs: Return the graph with metadata flag
    - Disconnected graphs: Return the largest connected component with metadata
    
    Args:
        graph: The potentially degenerate graph
        strategy_name: Name of the strategy being executed (for logging)
    
    Returns:
        Tuple of (processed_graph, metadata_dict)
        metadata_dict contains:
            - 'is_degenerate': bool
            - 'degeneracy_reasons': list of strings
            - 'original_num_nodes': int
            - 'original_num_edges': int
            - 'processed_num_nodes': int
            - 'processed_num_edges': int
            - 'component_info': dict with component details if applicable
    """
    original_num_nodes = graph.number_of_nodes()
    original_num_edges = graph.number_of_edges()
    
    is_degenerate, reasons = detect_degenerate_graph(graph)
    
    metadata = {
        'is_degenerate': is_degenerate,
        'degeneracy_reasons': reasons,
        'original_num_nodes': original_num_nodes,
        'original_num_edges': original_num_edges,
        'processed_num_nodes': original_num_nodes,
        'processed_num_edges': original_num_edges,
        'component_info': {}
    }
    
    if not is_degenerate:
        logger.info(f"Graph is NOT degenerate. Proceeding with {strategy_name} strategy.")
        return graph, metadata
    
    logger.warning(f"DEGENERATE GRAPH detected for {strategy_name} strategy: {reasons}")
    
    processed_graph = graph.copy()
    
    if original_num_nodes == 0:
        # Empty graph - return as is
        metadata['degeneracy_flag'] = 'EMPTY'
        logger.warning(f"Empty graph encountered. Returning empty graph for {strategy_name}.")
        return processed_graph, metadata
    
    if original_num_nodes == 1:
        # Single node - return as is but flag it
        metadata['degeneracy_flag'] = 'SINGLE_NODE'
        logger.warning(f"Single-node graph encountered. Returning single node for {strategy_name}.")
        return processed_graph, metadata
    
    if len(reasons) > 0 and "DISCONNECTED" in reasons[0]:
        # Disconnected graph - extract largest connected component
        try:
            components = list(nx.strongly_connected_components(graph))
            if components:
                # Sort by size, largest first
                components.sort(key=len, reverse=True)
                largest_component = components[0]
                
                # Extract subgraph
                processed_graph = graph.subgraph(largest_component).copy()
                
                metadata['degeneracy_flag'] = 'DISCONNECTED_LARGEST_COMPONENT'
                metadata['component_info'] = {
                    'total_components': len(components),
                    'largest_component_size': len(largest_component),
                    'component_sizes': [len(c) for c in components]
                }
                
                metadata['processed_num_nodes'] = processed_graph.number_of_nodes()
                metadata['processed_num_edges'] = processed_graph.number_of_edges()
                
                logger.info(f"Extracted largest component ({len(largest_component)} nodes) "
                           f"from {len(components)} total components for {strategy_name}.")
        except nx.NetworkXError as e:
            logger.error(f"Error extracting largest component: {e}")
            metadata['degeneracy_flag'] = 'DISCONNECTED_ERROR'
    
    return processed_graph, metadata

def check_graph_connectivity(graph: nx.DiGraph, strategy_name: str = "unknown") -> Dict[str, Any]:
    """
    Check graph connectivity and return detailed information.
    
    This function is used by traversal strategies (full.py, lazy.py) to explicitly
    check for graph connectivity and log a "DEGENERATE" flag when appropriate.
    
    Args:
        graph: The graph to check
        strategy_name: Name of the calling strategy for logging context
    
    Returns:
        Dictionary with connectivity information:
            - 'is_connected': bool
            - 'is_degenerate': bool
            - 'degeneracy_reasons': list of strings
            - 'num_components': int
            - 'largest_component_size': int
            - 'degenerate_flag': str or None
    """
    result = {
        'is_connected': False,
        'is_degenerate': False,
        'degeneracy_reasons': [],
        'num_components': 0,
        'largest_component_size': 0,
        'degenerate_flag': None
    }
    
    num_nodes = graph.number_of_nodes()
    
    if num_nodes == 0:
        result['is_degenerate'] = True
        result['degeneracy_reasons'].append("EMPTY_GRAPH")
        result['degenerate_flag'] = "DEGENERATE"
        logger.warning(f"[{strategy_name}] Graph is empty - DEGENERATE flag set.")
        return result
    
    if num_nodes == 1:
        result['is_degenerate'] = True
        result['degeneracy_reasons'].append("SINGLE_NODE")
        result['degenerate_flag'] = "DEGENERATE"
        logger.warning(f"[{strategy_name}] Graph has only one node - DEGENERATE flag set.")
        result['num_components'] = 1
        result['largest_component_size'] = 1
        return result
    
    try:
        components = list(nx.strongly_connected_components(graph))
        result['num_components'] = len(components)
        result['largest_component_size'] = max(len(c) for c in components) if components else 0
        
        if len(components) == 1 and num_nodes > 0:
            result['is_connected'] = True
            logger.debug(f"[{strategy_name}] Graph is fully connected ({num_nodes} nodes).")
        else:
            result['is_connected'] = False
            result['is_degenerate'] = True
            result['degeneracy_reasons'].append(f"DISCONNECTED_{len(components)}_COMPONENTS")
            result['degenerate_flag'] = "DEGENERATE"
            logger.warning(f"[{strategy_name}] Graph is disconnected ({len(components)} components) - DEGENERATE flag set.")
            
    except nx.NetworkXError as e:
        logger.error(f"[{strategy_name}] Error checking connectivity: {e}")
        result['is_degenerate'] = True
        result['degeneracy_reasons'].append(f"CONNECTIVITY_ERROR_{str(e)}")
        result['degenerate_flag'] = "DEGENERATE"
    
    return result