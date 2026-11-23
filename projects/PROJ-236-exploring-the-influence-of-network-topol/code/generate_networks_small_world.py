"""
Small‑World (Watts‑Strogatz) graph generator utilities.

This module provides a thin wrapper around :func:`networkx.watts_strogatz_graph`
that is used by the US1 small‑world topology generation pipeline.  The function
is deliberately simple – it creates a graph with the requested number of nodes,
average degree, and rewiring probability and returns the NetworkX graph object.
The surrounding pipeline (e.g. distance‑cutoff logic) can further process the
graph, but for the unit‑test that validates the clustering coefficient we only
need the raw Watts‑Strogatz graph.

The implementation is pure Python and has no external side‑effects, making it
safe to import from any part of the codebase.
"""

from __future__ import annotations

import networkx as nx
from typing import Any

__all__ = ["generate_small_world_graph"]

def generate_small_world_graph(
    num_nodes: int,
    avg_degree: int,
    rewiring_prob: float,
    *,
    seed: int | None = None,
    **_: Any,
) -> nx.Graph:
    """
    Generate a Watts‑Strogatz small‑world graph.

    Parameters
    ----------
    num_nodes: int
        Total number of nodes in the graph.
    avg_degree: int
        Each node is initially connected to ``avg_degree`` nearest neighbours
        (must be even, as required by the Watts‑Strogatz model).
    rewiring_prob: float
        Probability of rewiring each edge.  ``0`` yields a regular ring lattice,
        ``1`` yields a random graph.
    seed: int | None, optional
        Random seed for reproducibility.  If ``None`` the global NumPy RNG state
        is used.

    Returns
    -------
    nx.Graph
        The generated undirected Watts‑Strogatz graph.

    Notes
    -----
    The function validates its inputs and raises ``ValueError`` for illegal
    configurations (e.g. ``avg_degree`` not even or larger than ``num_nodes``).
    """
    if num_nodes <= 0:
        raise ValueError("num_nodes must be a positive integer")
    if avg_degree <= 0 or avg_degree >= num_nodes:
        raise ValueError(
            "avg_degree must be > 0 and < num_nodes (and even for the WS model)"
        )
    if avg_degree % 2 != 0:
        raise ValueError("avg_degree must be an even integer for Watts‑Strogatz")
    if not (0.0 <= rewiring_prob <= 1.0):
        raise ValueError("rewiring_prob must be between 0 and 1")

    # NetworkX implements the WS model directly.
    graph = nx.watts_strogatz_graph(
        n=num_nodes,
        k=avg_degree,
        p=rewiring_prob,
        seed=seed,
    )
    return graph