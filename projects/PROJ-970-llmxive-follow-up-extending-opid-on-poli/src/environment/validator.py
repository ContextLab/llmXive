"""
Validation utilities for ``StateGraph`` objects.
"""

import logging
from typing import Optional

import networkx as nx

from .state_graph import StateGraph

def validate_graph(sg: Optional[StateGraph]) -> None:
    """
    Validate that a ``StateGraph`` has a reachable path from its start node
    to its goal node.

    Raises
    ------
    ValueError
        If ``sg`` is ``None``.
    RuntimeError
        If no path exists from ``sg.start`` to ``sg.goal``.
    """
    if sg is None:
        raise ValueError("StateGraph must not be None")
    if not sg.is_valid():
        raise RuntimeError(f"Graph {sg.graph_id} is invalid: no path from start to goal")