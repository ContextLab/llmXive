"""
Additional network generators for the project.

This module provides the Erdős‑Rényi (random) graph generator required by
task T023.  The function is deliberately kept lightweight and relies on the
core utilities already defined in ``code/generate_networks.py`` such as
``nearest_neighbor_distance`` and ``generate_connected_graph``.
"""

from __future__ import annotations

import itertools
from typing import Tuple

import numpy as np
import networkx as nx
from scipy.spatial.distance import cdist

# Import utilities from the main generate_networks module.
# The import is placed here to avoid circular‑import problems: the main module
# imports this file *after* it has defined its own public symbols.
from generate_networks import (
    nearest_neighbor_distance,
    generate_connected_graph,
)

def generate_random_graph(
    num_nodes: int,
    edge_prob: float,
    positions: np.ndarray,
    cutoff_factor: float = 1.0,
    max_attempts: int = 10,
) -> nx.Graph:
    """
    Generate an Erdős‑Rényi (G(n, p)) graph with optional distance‑cutoff
    filtering.

    Parameters
    ----------
    num_nodes : int
        Number of nodes (must match ``positions.shape[0]``).
    edge_prob : float
        Probability of creating an edge between any pair of nodes.
    positions : np.ndarray
        Array of shape ``(num_nodes, d)`` containing the spatial coordinates
        of each node.  The positions are stored as a node attribute ``"pos"``.
    cutoff_factor : float, optional
        Multiply the nearest‑neighbor distance by this factor to obtain a
        maximum allowed Euclidean distance for an edge.  Edges longer than
        this threshold are removed after the random graph is generated.
        The default ``1.0`` applies no additional cutoff.
    max_attempts : int, optional
        Number of attempts to obtain a connected graph before falling back
        to the deterministic ``generate_connected_graph`` helper.

    Returns
    -------
    nx.Graph
        A connected Erdős‑Rényi graph respecting the distance cutoff.

    Raises
    ------
    ValueError
        If ``num_nodes`` is non‑positive or ``edge_prob`` is outside ``[0, 1]``.
    """
    if num_nodes <= 0:
        raise ValueError("num_nodes must be a positive integer")
    if not (0.0 <= edge_prob <= 1.0):
        raise ValueError("edge_prob must be between 0 and 1")

    # Pre‑compute the distance matrix once – it will be reused for edge
    # filtering if a cutoff is requested.
    distance_matrix = cdist(positions, positions)
    nn_dist = nearest_neighbor_distance(positions)
    max_allowed_dist = cutoff_factor * nn_dist

    for attempt in range(max_attempts):
        # Create the raw Erdős‑Rényi graph.
        G = nx.erdos_renyi_graph(num_nodes, edge_prob)

        # Attach position data to each node for downstream analysis.
        for idx, pos in enumerate(positions):
            G.nodes[idx]["pos"] = pos

        # Apply the distance cutoff if the factor is not the default.
        if cutoff_factor != 1.0:
            # Identify edges that violate the distance constraint.
            too_long = [
                (i, j)
                for i, j in G.edges
                if distance_matrix[i, j] > max_allowed_dist
            ]
            if too_long:
                G.remove_edges_from(too_long)

        # Verify connectivity; if satisfied, return the graph.
        if nx.is_connected(G):
            return G

    # If we reach this point the random attempts failed to produce a
    # connected graph.  As a safe fallback we delegate to the deterministic
    # connectivity routine which guarantees a spanning graph while still
    # respecting the cutoff.
    return generate_connected_graph(num_nodes, positions, cutoff_factor)
