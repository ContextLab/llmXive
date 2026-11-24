"""
Data structures for the synthetic State‑Graph environments.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
import networkx as nx

@dataclass
class Node:
    id: str
    state_value: Any
    is_goal: bool = False
    reward: float = 0.0

@dataclass
class Edge:
    source: str
    target: str
    prob: float = 1.0
    reward: float = 0.0

@dataclass
class StateGraph:
    tier: int
    graph_id: str = field(default_factory=lambda: f"graph_{random.randint(0, 1_000_000)}")
    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)
    start: Optional[str] = None
    goal: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_valid(self) -> bool:
        """Return ``True`` if there exists a directed path from ``start`` to ``goal``."""
        if self.start is None or self.goal is None:
            return False
        G = nx.DiGraph()
        for edge in self.edges:
            G.add_edge(edge.source, edge.target, weight=edge.prob)
        try:
            nx.shortest_path(G, source=self.start, target=self.goal)
            return True
        except nx.NetworkXNoPath:
            return False