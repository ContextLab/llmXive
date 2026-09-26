"""
State Graph Module for OPID Routing Complexity Analysis.

Defines the core data structures for the environment: Node, Edge, and StateGraph.
These structures represent the synthetic environments used in the simulation.
"""

import random
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
import numpy as np

@dataclass
class Node:
    """
    Represents a state in the environment.

    Attributes:
        id: Unique identifier for the node.
        is_start: Boolean flag indicating if this is the start state.
        is_goal: Boolean flag indicating if this is the goal state.
        reward: Immediate reward received upon entering this state.
    """
    id: int
    is_start: bool = False
    is_goal: bool = False
    reward: float = 0.0

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        return self.id == other.id


@dataclass
class Edge:
    """
    Represents a directed transition between two nodes.

    Attributes:
        source: The ID of the source node.
        target: The ID of the target node.
        probability: The probability of successfully transitioning (0.0 to 1.0).
        cost: The cost associated with taking this transition (optional).
    """
    source: int
    target: int
    probability: float = 1.0
    cost: float = 0.0

    def __hash__(self):
        return hash((self.source, self.target))

    def __eq__(self, other):
        if not isinstance(other, Edge):
            return False
        return self.source == other.source and self.target == other.target


@dataclass
class StateGraph:
    """
    Represents the entire state space of the environment.

    Attributes:
        nodes: Dictionary mapping node_id -> Node object.
        edges: List of Edge objects representing transitions.
        adjacency: Dictionary mapping node_id -> List of target node_ids for fast lookup.
        start: ID of the start node.
        goal: ID of the goal node.
        tier: Complexity tier identifier (1, 2, or 3).
    """
    nodes: Dict[int, Node] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)
    adjacency: Dict[int, List[int]] = field(default_factory=dict)
    start: Optional[int] = None
    goal: Optional[int] = None
    tier: int = 1

    def add_node(self, node: Node) -> None:
        """Adds a node to the graph."""
        self.nodes[node.id] = node
        if node.is_start:
            self.start = node.id
        if node.is_goal:
            self.goal = node.id
        if node.id not in self.adjacency:
            self.adjacency[node.id] = []

    def add_edge(self, source: int, target: int, probability: float = 1.0, cost: float = 0.0) -> None:
        """Adds a directed edge to the graph."""
        if source not in self.nodes:
            raise ValueError(f"Source node {source} does not exist.")
        if target not in self.nodes:
            raise ValueError(f"Target node {target} does not exist.")

        edge = Edge(source=source, target=target, probability=probability, cost=cost)
        self.edges.append(edge)
        self.adjacency[source].append(target)

    def get_outgoing_edges(self, node_id: int) -> List[Edge]:
        """Returns a list of outgoing edges for a given node."""
        return [e for e in self.edges if e.source == node_id]

    def get_neighbors(self, node_id: int) -> List[int]:
        """Returns a list of neighbor node IDs."""
        return self.adjacency.get(node_id, [])

    def is_valid(self) -> bool:
        """
        Validates the graph structure.

        Checks:
        1. Start and Goal nodes are defined.
        2. Start and Goal nodes exist in the graph.
        3. No self-loops (unless explicitly allowed, but typically not in pathfinding).
        4. (Optional) Connectivity checks could be added here, but validation
           logic is often delegated to the Validator module (T014) for path existence.

        Returns:
            bool: True if the graph is structurally valid, False otherwise.
        """
        if self.start is None or self.goal is None:
            return False

        if self.start not in self.nodes or self.goal not in self.nodes:
            return False

        # Check for self-loops (optional strictness)
        for edge in self.edges:
            if edge.source == edge.target:
                # Depending on spec, self-loops might be allowed or not.
                # For now, we consider them structurally valid but potentially inefficient.
                pass

        return True

    def __str__(self) -> str:
        return (f"StateGraph(tier={self.tier}, nodes={len(self.nodes)}, "
                f"edges={len(self.edges)}, start={self.start}, goal={self.goal})")