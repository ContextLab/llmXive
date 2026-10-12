"""
Validator for StateGraph objects.

This module provides a single function ``validate_graph`` that checks whether a
``StateGraph`` instance contains a reachable path from its ``start`` node to its
``goal`` node.  If the graph is invalid, a ``RuntimeError`` is raised; otherwise
the function returns ``None``.  ``ValueError`` is raised for malformed inputs.
"""

import logging
from typing import Optional

import networkx as nx

from environment.state_graph import StateGraph

log = logging.getLogger(__name__)

def validate_graph(sg: Optional[StateGraph]) -> None:
    """
    Validate that a ``StateGraph`` has a reachable path from its start node to its goal node.

    Parameters
    ----------
    sg : StateGraph or None
        The graph to validate.

    Raises
    ------
    ValueError
        If ``sg`` is ``None`` or missing required attributes.
    RuntimeError
        If no path exists from ``sg.start`` to ``sg.goal``.
    """
    if sg is None:
        raise ValueError("StateGraph is None")

    # Verify that the essential attributes exist
    if not hasattr(sg, "start") or not hasattr(sg, "goal"):
        raise ValueError("StateGraph missing required 'start' or 'goal' attributes")

    # Build a directed NetworkX graph from the StateGraph definition
    G = nx.DiGraph()
    for node in getattr(sg, "nodes", []):
        # Assume each node has a unique identifier attribute ``id``
        node_id = getattr(node, "id", None)
        if node_id is None:
            raise ValueError("Node missing 'id' attribute")
        G.add_node(node_id)

    for edge in getattr(sg, "edges", []):
        # Assume each edge has ``source`` and ``target`` attributes identifying node ids
        source = getattr(edge, "source", None)
        target = getattr(edge, "target", None)
        if source is None or target is None:
            raise ValueError("Edge missing 'source' or 'target' attribute")
        G.add_edge(source, target)

    # Use NetworkX to check for a path from start to goal
    if not nx.has_path(G, sg.start, sg.goal):
        raise RuntimeError(
            f"No path from start node {sg.start} to goal node {sg.goal} in StateGraph {getattr(sg, 'graph_id', '<unknown>')}"
        )

    # If validation passes, log at debug level
    log.debug(
        "StateGraph %s passed validation (start=%s, goal=%s)",
        getattr(sg, "graph_id", "<unknown>"),
        sg.start,
        sg.goal,
    )