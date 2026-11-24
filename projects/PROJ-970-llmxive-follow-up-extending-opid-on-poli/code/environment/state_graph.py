"""
src/environment/state_graph.py

Data structures representing a synthetic state‑graph environment.

This module defines three public names:
  - ``Node`` – a dataclass representing a graph node.
  - ``Edge`` – a dataclass representing a directed edge between two nodes.
  - ``StateGraph`` – a dataclass encapsulating a full environment graph.

The ``StateGraph.is_valid`` method builds a ``networkx.DiGraph`` from the
stored ``nodes`` and ``edges`` and checks that a directed path exists from
``start`` to ``goal``.  It returns ``True`` when such a path exists and
raises ``RuntimeError`` when the internal representation is malformed.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
import networkx as nx


@dataclass(frozen=True)
class Node:
    """
    Representation of a node in a ``StateGraph``.

    Attributes
    ----------
    node_id : int | str
        Unique identifier for the node.  ``int`` is used throughout the
        code base, but ``str`` is accepted for flexibility.
    reward : float, default 0.0
        Immediate reward associated with visiting the node.  Most tiers use
        sparse rewards, so the default is zero.
    metadata : dict, optional
        Arbitrary auxiliary information (e.g. feature vectors).  Not used
        by the core simulation but kept for extensibility.
    """
    node_id: int | str
    reward: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Edge:
    """
    Representation of a directed edge in a ``StateGraph``.

    Attributes
    ----------
    source : int | str
        Identifier of the tail node.
    target : int | str
        Identifier of the head node.
    probability : float, default 1.0
        Transition probability for stochastic environments.  For deterministic
        tiers this should be ``1.0``; for stochastic tiers it lies in (0, 1].
    metadata : dict, optional
        Additional edge‑level information (e.g. cost, label).
    """
    source: int | str
    target: int | str
    probability: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not (0.0 < self.probability <= 1.0):
            raise ValueError(
                f"Edge probability must be in (0, 1], got {self.probability}"
            )


@dataclass
class StateGraph:
    """
    Container for a synthetic environment graph.

    Parameters
    ----------
    graph_id : str
        Human‑readable identifier (e.g. ``tier1_0001``).
    tier : int
        Complexity tier (1, 2 or 3).
    nodes : List[Node]
        All nodes that belong to the graph.
    edges : List[Edge]
        Directed edges connecting the nodes.
    start : int | str
        Identifier of the start node.
    goal : int | str
        Identifier of the goal node.
    metadata : dict, optional
        Arbitrary key‑value pairs describing the graph (e.g. creation time,
        seed used, reward sparsity, etc.).
    """
    graph_id: str
    tier: int
    nodes: List[Node] = field(default_factory=list)
    edges: List[Edge] = field(default_factory=list)
    start: Optional[int | str] = None
    goal: Optional[int | str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Basic sanity checks – they raise early so that callers (e.g.
        # graph_generator) get a clear error instead of a silent failure.
        if not self.nodes:
            raise RuntimeError("StateGraph must contain at least one node.")
        node_ids = {n.node_id for n in self.nodes}
        if self.start is None or self.goal is None:
            raise RuntimeError("Both start and goal node identifiers must be set.")
        if self.start not in node_ids:
            raise RuntimeError(f"Start node '{self.start}' not present in node list.")
        if self.goal not in node_ids:
            raise RuntimeError(f"Goal node '{self.goal}' not present in node list.")

    def is_valid(self) -> bool:
        """
        Validate the graph structure.

        Returns
        -------
        bool
            ``True`` if a directed path exists from ``start`` to ``goal``.
            ``False`` otherwise.

        Notes
        -----
        The method builds a temporary ``networkx.DiGraph`` from the stored
        ``nodes`` and ``edges``.  Edge probabilities are stored as edge
        attributes but do not affect the reachability check – any edge with
        a non‑zero probability is considered traversable.
        """
        # Build a directed graph.
        G = nx.DiGraph()
        # Add nodes.
        for node in self.nodes:
            G.add_node(node.node_id)
        # Add edges – only keep edges with a positive probability.
        for edge in self.edges:
            if edge.probability > 0.0:
                G.add_edge(edge.source, edge.target, probability=edge.probability)
        # Use NetworkX's path existence test.
        try:
            reachable = nx.has_path(G, self.start, self.goal)
        except nx.NetworkXError as exc:
            raise RuntimeError(
                f"Invalid start/goal identifiers for graph '{self.graph_id}': {exc}"
            ) from exc
        return reachable

    # Convenience helpers -------------------------------------------------
    def to_networkx(self) -> nx.DiGraph:
        """
        Convert the ``StateGraph`` into a ``networkx.DiGraph`` instance.
        Edge probabilities are stored under the ``probability`` attribute.

        Returns
        -------
        networkx.DiGraph
        """
        G = nx.DiGraph()
        for node in self.nodes:
            G.add_node(node.node_id, reward=node.reward, **node.metadata)
        for edge in self.edges:
            G.add_edge(
                edge.source,
                edge.target,
                probability=edge.probability,
                **edge.metadata,
            )
        return G

    def __repr__(self) -> str:
        return (
            f"StateGraph(id={self.graph_id!r}, tier={self.tier}, "
            f"nodes={len(self.nodes)}, edges={len(self.edges)}, "
            f"start={self.start!r}, goal={self.goal!r})"
        )