"""
Data integrity validators for network synchronization analysis.

This module provides functions to validate graph structures, simulation inputs,
and network lists to ensure data integrity before processing.
"""

import logging
from typing import Dict, Any, List, Tuple, Optional, Union
import networkx as nx
import numpy as np
from data_models import NetworkGraph

logger = logging.getLogger(__name__)


def check_disconnected_graph(G: nx.Graph) -> Tuple[bool, int]:
    """
    Check if a graph is disconnected and count connected components.

    Args:
        G: A NetworkX graph to check.

    Returns:
        Tuple of (is_disconnected, num_components).
        is_disconnected is True if the graph has more than 1 connected component.
    """
    if G.number_of_nodes() == 0:
        logger.warning("Graph has no nodes.")
        return True, 0

    components = list(nx.connected_components(G))
    num_components = len(components)
    is_disconnected = num_components > 1

    if is_disconnected:
        logger.warning(f"Graph is disconnected with {num_components} components.")
    else:
        logger.info("Graph is connected.")

    return is_disconnected, num_components


def validate_graph(
    G: nx.Graph,
    min_nodes: int = 2,
    max_nodes: Optional[int] = None,
    allow_self_loops: bool = False,
    allow_multi_edges: bool = False
) -> Tuple[bool, List[str]]:
    """
    Validate a graph for structural integrity and constraints.

    Args:
        G: The NetworkX graph to validate.
        min_nodes: Minimum allowed number of nodes.
        max_nodes: Maximum allowed number of nodes (None for no limit).
        allow_self_loops: Whether self-loops are allowed.
        allow_multi_edges: Whether multi-edges are allowed (for MultiGraph).

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []

    # Check node count
    num_nodes = G.number_of_nodes()
    if num_nodes < min_nodes:
        errors.append(f"Graph has {num_nodes} nodes, minimum is {min_nodes}.")

    if max_nodes is not None and num_nodes > max_nodes:
        errors.append(f"Graph has {num_nodes} nodes, maximum is {max_nodes}.")

    # Check for self-loops
    if not allow_self_loops:
        self_loops = list(nx.selfloop_edges(G))
        if self_loops:
            errors.append(f"Graph contains {len(self_loops)} self-loops, which are not allowed.")

    # Check for multi-edges (if using a Graph, this is naturally handled, but check if MultiGraph)
    if not allow_multi_edges and isinstance(G, nx.MultiGraph):
        multi_edges = [e for e in G.edges(keys=True) if G.number_of_edges(*e[:2]) > 1]
        if multi_edges:
            errors.append(f"Graph contains {len(multi_edges)} multi-edges, which are not allowed.")

    # Check for isolated nodes (optional, but useful for simulation)
    isolated = [n for n, d in G.degree() if d == 0]
    if isolated:
        logger.warning(f"Graph contains {len(isolated)} isolated nodes: {isolated[:5]}...")
        # Not an error, just a warning

    # Check edge weights if present
    if G.number_of_edges() > 0:
        first_edge = next(iter(G.edges(data=True)))
        if 'weight' in first_edge[2]:
            weights = [d.get('weight', 1.0) for u, v, d in G.edges(data=True)]
            if any(w <= 0 for w in weights):
                errors.append("Graph contains non-positive edge weights.")

    is_valid = len(errors) == 0
    if not is_valid:
        logger.error(f"Graph validation failed: {errors}")
    else:
        logger.info("Graph validation passed.")

    return is_valid, errors


def validate_network_list(
    networks: List[Union[nx.Graph, NetworkGraph]],
    min_networks: int = 1
) -> Tuple[bool, List[str]]:
    """
    Validate a list of networks.

    Args:
        networks: List of NetworkX graphs or NetworkGraph dataclasses.
        min_networks: Minimum number of networks required.

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []

    if len(networks) < min_networks:
        errors.append(f"Expected at least {min_networks} networks, got {len(networks)}.")
        return False, errors

    valid_count = 0
    for i, net in enumerate(networks):
        if isinstance(net, NetworkGraph):
            g = net.graph
        elif isinstance(net, nx.Graph):
            g = net
        else:
            errors.append(f"Network at index {i} is not a valid graph type.")
            continue

        is_valid, sub_errors = validate_graph(g)
        if not is_valid:
            errors.extend([f"Network {i}: {e}" for e in sub_errors])
        else:
            valid_count += 1

    if valid_count == 0:
        errors.append("No valid networks found in the list.")

    is_valid = len(errors) == 0
    if not is_valid:
        logger.error(f"Network list validation failed with {len(errors)} errors.")
    else:
        logger.info(f"Network list validation passed. {valid_count} valid networks.")

    return is_valid, errors


def validate_simulation_inputs(
    k_values: List[float],
    dt: float = 0.01,
    t_max: float = 100.0
) -> Tuple[bool, List[str]]:
    """
    Validate simulation parameters.

    Args:
        k_values: List of coupling strength values to sweep.
        dt: Time step for integration.
        t_max: Maximum simulation time.

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []

    if not k_values:
        errors.append("k_values list cannot be empty.")
    else:
        if any(k < 0 for k in k_values):
            errors.append("Coupling strength (k) cannot be negative.")
        if len(k_values) != len(set(k_values)):
            logger.warning("k_values contains duplicates.")

    if dt <= 0:
        errors.append("Time step (dt) must be positive.")
    if dt > 0.1:
        logger.warning(f"Time step (dt={dt}) is large; simulation may be unstable.")

    if t_max <= 0:
        errors.append("Maximum simulation time (t_max) must be positive.")

    is_valid = len(errors) == 0
    if not is_valid:
        logger.error(f"Simulation input validation failed: {errors}")
    else:
        logger.info("Simulation input validation passed.")

    return is_valid, errors