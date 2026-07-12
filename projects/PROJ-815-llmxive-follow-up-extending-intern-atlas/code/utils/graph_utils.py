"""
Graph utilities for the llmXive Intern-Atlas follow-up project.

Provides functions for loading graph structures, filtering edges by type,
validating metadata, and enforcing the constraint that no LLM-inferred
edges are present in the analysis pipeline.
"""

import sys
from typing import Any, Dict, List, Optional, Set, Tuple, Union

try:
    import networkx as nx
except ImportError:
    # Fallback if networkx is not installed, though requirements.txt should handle this
    nx = None  # type: ignore

from code.utils.constants import EDGE_TYPES, LLM_INFERRRED_EDGE_TYPE, RETRACTION_LABELS

def load_graph_from_gml(path: str) -> nx.Graph:
    """
    Load a graph from a GML file.

    Args:
        path: Path to the .gml file.

    Returns:
        A networkx Graph object.

    Raises:
        FileNotFoundError: If the file does not exist.
        ImportError: If networkx is not installed.
    """
    if nx is None:
        raise ImportError("networkx is required to load graphs. Install via pip.")
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Graph file not found: {path}")
    
    return nx.read_gml(path)


def filter_edges_by_type(
    G: nx.Graph, 
    allowed_types: Optional[Set[str]] = None
) -> List[Tuple[Any, Any, Dict[str, Any]]]:
    """
    Filter edges based on their 'type' attribute.

    Args:
        G: The networkx graph.
        allowed_types: A set of allowed edge type strings (e.g., {'improves', 'replaces'}).
                       If None, returns all edges.

    Returns:
        A list of edge tuples (u, v, data_dict) that match the allowed types.
    """
    if allowed_types is None:
        return list(G.edges(data=True))
    
    filtered_edges = []
    for u, v, data in G.edges(data=True):
        edge_type = data.get('type')
        if edge_type in allowed_types:
            filtered_edges.append((u, v, data))
    
    return filtered_edges


def validate_edge_metadata(G: nx.Graph) -> Dict[str, Any]:
    """
    Validate that all edges have the required metadata attributes.

    Checks for the presence of 'type' and 'year' attributes on edges.

    Args:
        G: The networkx graph.

    Returns:
        A dictionary with validation results:
            {
                "valid": bool,
                "missing_type_count": int,
                "missing_year_count": int,
                "invalid_types": Set[str]
            }
    """
    missing_type = 0
    missing_year = 0
    invalid_types = set()

    for u, v, data in G.edges(data=True):
        if 'type' not in data:
            missing_type += 1
        else:
            if data['type'] not in EDGE_TYPES:
                invalid_types.add(data['type'])
        
        if 'year' not in data:
            missing_year += 1

    return {
        "valid": (missing_type == 0 and missing_year == 0 and len(invalid_types) == 0),
        "missing_type_count": missing_type,
        "missing_year_count": missing_year,
        "invalid_types": list(invalid_types)
    }


def abort_if_llm_inferred(G: nx.Graph) -> None:
    """
    Check the graph for any edges marked as LLM-inferred.
    
    If any such edge is found, the function halts execution with a clear
    error message and exit code 1, as per FR-002.
    
    This function assumes that LLM-inferred edges are marked with a specific
    type constant defined in code.utils.constants (e.g., 'llm_inferred').
    
    Args:
        G: The networkx graph to check.
        
    Raises:
        SystemExit: If LLM-inferred edges are detected.
    """
    llm_inferred_type = LLM_INFERRRED_EDGE_TYPE
    found_count = 0
    sample_nodes = []

    for u, v, data in G.edges(data=True):
        if data.get('type') == llm_inferred_type:
            found_count += 1
            if len(sample_nodes) < 3:
                sample_nodes.append((u, v))

    if found_count > 0:
        msg = (
            f"CRITICAL ERROR: Detected {found_count} edge(s) marked as LLM-inferred "
            f"(type='{llm_inferred_type}'). "
            "Per FR-002, analysis cannot proceed with LLM-inferred edge types. "
            "Please filter the dataset to include only human-annotated edges.\n"
        )
        if sample_nodes:
            msg += f"Sample LLM-inferred edges found: {sample_nodes}\n"
        
        print(msg, file=sys.stderr)
        sys.exit(1)

def get_edge_type_distribution(G: nx.Graph) -> Dict[str, int]:
    """
    Count the occurrences of each edge type in the graph.

    Args:
        G: The networkx graph.

    Returns:
        A dictionary mapping edge type strings to their counts.
    """
    distribution: Dict[str, int] = {}
    for u, v, data in G.edges(data=True):
        edge_type = data.get('type', 'unknown')
        distribution[edge_type] = distribution.get(edge_type, 0) + 1
    return distribution

def filter_nodes_by_year(G: nx.Graph, min_year: int, max_year: int) -> Set[Any]:
    """
    Return a set of node IDs that have a 'year' attribute within the specified range.
    
    This is useful for pre-filtering nodes before feature extraction.
    
    Args:
        G: The networkx graph.
        min_year: Inclusive minimum year.
        max_year: Inclusive maximum year.
        
    Returns:
        A set of node IDs within the date range.
    """
    valid_nodes = set()
    for node, data in G.nodes(data=True):
        year = data.get('year')
        if year is not None and min_year <= year <= max_year:
            valid_nodes.add(node)
    return valid_nodes
    
import os