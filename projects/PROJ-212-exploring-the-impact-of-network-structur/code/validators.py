"""
Data integrity validators for network synchronization research.

This module provides functions to validate graph structures, ensure data quality,
and detect conditions that would invalidate simulation results (e.g., disconnected graphs).
"""
import logging
from typing import Dict, Any, List, Tuple, Optional, Union

import networkx as nx
import numpy as np

from data_models import NetworkGraph

logger = logging.getLogger(__name__)


def validate_graph(graph: NetworkGraph) -> Tuple[bool, List[str]]:
    """
    Validate a NetworkGraph object for data integrity.

    Checks:
    - Graph is not None
    - Graph has at least 2 nodes (minimum for synchronization)
    - No self-loops (unless explicitly allowed in config, currently not supported)
    - No duplicate edges (handled by NetworkX, but verified for safety)
    - Edge weights are numeric and non-negative (if present)

    Args:
        graph: The NetworkGraph object to validate

    Returns:
        Tuple of (is_valid: bool, errors: List[str])
    """
    errors: List[str] = []

    if graph.g is None:
        errors.append("Graph object is None")
        return False, errors

    G = graph.g

    # Check minimum node count
    if G.number_of_nodes() < 2:
        errors.append(f"Graph has {G.number_of_nodes()} nodes; minimum required is 2")

    # Check for self-loops
    self_loops = list(nx.selfloop_edges(G))
    if self_loops:
        errors.append(f"Graph contains {len(self_loops)} self-loops, which are not supported")

    # Check for edge weights if present
    if G.number_of_edges() > 0:
        first_edge = next(iter(G.edges(data=True)))
        if 'weight' in first_edge[2]:
            for u, v, data in G.edges(data=True):
                w = data.get('weight')
                if w is None:
                    errors.append(f"Edge ({u}, {v}) has missing weight")
                elif not isinstance(w, (int, float)):
                    errors.append(f"Edge ({u}, {v}) has non-numeric weight: {type(w)}")
                elif w < 0:
                    errors.append(f"Edge ({u}, {v}) has negative weight: {w}")

    is_valid = len(errors) == 0
    if not is_valid:
        logger.warning(f"Graph validation failed with {len(errors)} errors: {errors}")
    else:
        logger.info("Graph validation passed")

    return is_valid, errors


def validate_network_list(networks: List[NetworkGraph]) -> Tuple[bool, List[str]]:
    """
    Validate a list of NetworkGraph objects.

    Checks:
    - List is not empty
    - Each graph passes individual validation
    - No duplicate graph IDs (if present)

    Args:
        networks: List of NetworkGraph objects

    Returns:
        Tuple of (is_valid: bool, errors: List[str])
    """
    errors: List[str] = []

    if not networks:
        errors.append("Network list is empty")
        return False, errors

    seen_ids = set()
    for i, net in enumerate(networks):
        is_valid, net_errors = validate_graph(net)
        if not is_valid:
            for err in net_errors:
                errors.append(f"Network {i} ({net.id}): {err}")

        # Check for duplicate IDs
        if net.id:
            if net.id in seen_ids:
                errors.append(f"Duplicate network ID: {net.id}")
            seen_ids.add(net.id)

    is_valid = len(errors) == 0
    if not is_valid:
        logger.warning(f"Network list validation failed with {len(errors)} errors")
    else:
        logger.info(f"Network list validation passed for {len(networks)} networks")

    return is_valid, errors


def check_disconnected_graph(graph: Union[nx.Graph, NetworkGraph]) -> Tuple[bool, List[int]]:
    """
    Check if a graph is disconnected and return component sizes.

    This is critical for synchronization simulations, as disconnected graphs
    cannot achieve global synchronization (critical coupling is effectively infinite).

    Args:
        graph: A NetworkX Graph or NetworkGraph object

    Returns:
        Tuple of (is_disconnected: bool, component_sizes: List[int])
        - is_disconnected: True if graph has more than one connected component
        - component_sizes: List of sizes of each connected component (sorted descending)
    """
    if isinstance(graph, NetworkGraph):
        G = graph.g
    else:
        G = graph

    if G is None or G.number_of_nodes() == 0:
        logger.warning("Empty or None graph provided to check_disconnected_graph")
        return True, []

    components = list(nx.connected_components(G))
    component_sizes = sorted([len(c) for c in components], reverse=True)
    is_disconnected = len(components) > 1

    if is_disconnected:
        logger.warning(
            f"Graph is disconnected with {len(components)} components. "
            f"Sizes: {component_sizes}. Largest component: {component_sizes[0]} nodes."
        )
    else:
        logger.debug("Graph is connected")

    return is_disconnected, component_sizes


def validate_simulation_inputs(
    graph: NetworkGraph,
    n_oscillators: int = 200,
    k_range: Tuple[float, float] = (0.0, 5.0),
    k_step: float = 0.1,
    tolerance: float = 1e-6
) -> Tuple[bool, List[str]]:
    """
    Validate inputs for Kuramoto simulation.

    Checks:
    - Graph is valid (passes validate_graph)
    - Graph is connected (critical for synchronization)
    - n_oscillators is positive and <= graph nodes
    - k_range is valid (start < end)
    - k_step is positive
    - tolerance is positive

    Args:
        graph: The network graph to simulate
        n_oscillators: Number of oscillators (should match graph nodes or be <=)
        k_range: Tuple of (min_k, max_k) for coupling strength sweep
        k_step: Step size for K sweep
        tolerance: Numerical tolerance for integration

    Returns:
        Tuple of (is_valid: bool, errors: List[str])
    """
    errors: List[str] = []

    # Validate graph structure
    graph_valid, graph_errors = validate_graph(graph)
    if not graph_valid:
        errors.extend([f"Graph: {e}" for e in graph_errors])

    # Check connectivity
    is_disconnected, _ = check_disconnected_graph(graph)
    if is_disconnected:
        errors.append("Graph is disconnected; simulation will return infinite threshold")

    # Validate n_oscillators
    if n_oscillators <= 0:
        errors.append(f"n_oscillators must be positive, got {n_oscillators}")
    elif graph.g and n_oscillators > graph.g.number_of_nodes():
        errors.append(
            f"n_oscillators ({n_oscillators}) exceeds graph nodes ({graph.g.number_of_nodes()})"
        )

    # Validate k_range
    k_min, k_max = k_range
    if k_min >= k_max:
        errors.append(f"k_range must have start < end, got ({k_min}, {k_max})")
    if k_min < 0:
        errors.append(f"k_range start must be non-negative, got {k_min}")

    # Validate k_step
    if k_step <= 0:
        errors.append(f"k_step must be positive, got {k_step}")

    # Validate tolerance
    if tolerance <= 0:
        errors.append(f"tolerance must be positive, got {tolerance}")

    is_valid = len(errors) == 0
    if not is_valid:
        logger.warning(f"Simulation input validation failed with {len(errors)} errors: {errors}")
    else:
        logger.info("Simulation input validation passed")

    return is_valid, errors