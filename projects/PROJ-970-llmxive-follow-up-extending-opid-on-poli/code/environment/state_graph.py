"""
State Graph implementation for OPID routing complexity analysis.

Defines the core data structures for state-space environments:
- Node: Represents a state in the graph
- Edge: Represents a transition between states with optional stochasticity
- StateGraph: The container graph with validation logic
"""
import random
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
import numpy as np


@dataclass
class Node:
    """Represents a state in the environment graph."""
    id: int
    reward: float = 0.0
    is_start: bool = False
    is_goal: bool = False

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        return self.id == other.id


@dataclass
class Edge:
    """Represents a transition between nodes with optional stochasticity."""
    source: Node
    target: Node
    probability: float = 1.0  # Stochastic transition probability
    action_id: int = 0  # Action that triggers this transition

    def __hash__(self):
        return hash((self.source.id, self.target.id, self.action_id))

    def __eq__(self, other):
        if not isinstance(other, Edge):
            return False
        return (self.source.id == other.source.id and
                self.target.id == other.target.id and
                self.action_id == other.action_id)


@dataclass
class StateGraph:
    """
    Container for the state-space environment graph.
    
    Attributes:
        nodes: List of all nodes in the graph
        edges: List of all edges (transitions) in the graph
        start: Reference to the starting node
        goal: Reference to the goal node
        tier: Complexity tier identifier (1, 2, or 3)
    """
    nodes: List[Node] = field(default_factory=list)
    edges: List[Edge] = field(default_factory=list)
    start: Optional[Node] = None
    goal: Optional[Node] = None
    tier: int = 1

    def get_node(self, node_id: int) -> Optional[Node]:
        """Retrieve a node by its ID."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def get_outgoing_edges(self, node: Node) -> List[Edge]:
        """Get all edges originating from a given node."""
        return [edge for edge in self.edges if edge.source == node]

    def get_incoming_edges(self, node: Node) -> List[Edge]:
        """Get all edges targeting a given node."""
        return [edge for edge in self.edges if edge.target == node]

    def is_valid(self) -> bool:
        """
        Validate that the graph is a well-formed environment.
        
        Checks:
        1. Start and goal nodes exist
        2. A path exists from start to goal (reachability)
        3. No duplicate nodes (by ID)
        4. All edges reference valid nodes
        
        Returns:
            bool: True if the graph is valid, False otherwise
        """
        # Check start and goal existence
        if self.start is None or self.goal is None:
            return False

        if self.start not in self.nodes or self.goal not in self.nodes:
            return False

        # Check for duplicate node IDs
        node_ids = [n.id for n in self.nodes]
        if len(node_ids) != len(set(node_ids)):
            return False

        # Check that all edges reference valid nodes
        valid_node_ids = {n.id for n in self.nodes}
        for edge in self.edges:
            if edge.source.id not in valid_node_ids:
                return False
            if edge.target.id not in valid_node_ids:
                return False

        # Check reachability from start to goal using BFS
        if not self._is_reachable(self.start, self.goal):
            return False

        return True

    def _is_reachable(self, start: Node, goal: Node) -> bool:
        """
        Check if there is a path from start to goal using BFS.
        
        Args:
            start: The starting node
            goal: The target node
            
        Returns:
            bool: True if goal is reachable from start, False otherwise
        """
        if start == goal:
            return True

        visited: Set[int] = set()
        queue: List[Node] = [start]
        visited.add(start.id)

        while queue:
            current = queue.pop(0)
            
            # Get outgoing edges with non-zero probability
            for edge in self.get_outgoing_edges(current):
                if edge.probability > 0:
                    neighbor = edge.target
                    if neighbor.id not in visited:
                        if neighbor == goal:
                            return True
                        visited.add(neighbor.id)
                        queue.append(neighbor)

        return False

    def __repr__(self):
        return (f"StateGraph(tier={self.tier}, nodes={len(self.nodes)}, "
                f"edges={len(self.edges)}, start={self.start.id if self.start else None}, "
                f"goal={self.goal.id if self.goal else None})")

    def to_dict(self) -> Dict[str, any]:
        """Serialize the graph to a dictionary for logging/checksums."""
        return {
            'tier': self.tier,
            'num_nodes': len(self.nodes),
            'num_edges': len(self.edges),
            'start_id': self.start.id if self.start else None,
            'goal_id': self.goal.id if self.goal else None,
            'nodes': [n.id for n in self.nodes],
            'edges': [(e.source.id, e.target.id, e.action_id) for e in self.edges]
        }