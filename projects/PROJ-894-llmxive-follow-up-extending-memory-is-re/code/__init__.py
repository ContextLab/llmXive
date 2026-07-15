# llmXive Project Package
# This file marks the 'code' directory as a Python package.

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import networkx as nx

@dataclass
class Task:
    """
    Represents a benchmark task (e.g., from LoCoMo).
    """
    task_id: str
    question: str
    context: str
    answer: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.task_id:
            raise ValueError("Task ID cannot be empty")

@dataclass
class MemoryGraph:
    """
    Wrapper around a NetworkX graph representing reconstructed memory.
    Includes utility methods for graph-based memory operations.
    """
    graph: nx.Graph
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_networkx(cls, nx_graph: nx.Graph, metadata: Optional[Dict[str, Any]] = None) -> 'MemoryGraph':
        return cls(graph=nx_graph, metadata=metadata or {})

    def add_node(self, node_id: str, **attrs):
        """Add a node to the memory graph."""
        self.graph.add_node(node_id, **attrs)

    def add_edge(self, u: str, v: str, **attrs):
        """Add an edge to the memory graph."""
        self.graph.add_edge(u, v, **attrs)

    def neighbors(self, node_id: str) -> List[str]:
        """Get neighbors of a node."""
        return list(self.graph.neighbors(node_id))

    def subgraph(self, nodes: List[str]) -> 'MemoryGraph':
        """Extract a subgraph containing the specified nodes."""
        sub_g = self.graph.subgraph(nodes)
        return MemoryGraph.from_networkx(sub_g, self.metadata)

    def node_count(self) -> int:
        return self.graph.number_of_nodes()

    def edge_count(self) -> int:
        return self.graph.number_of_edges()

@dataclass
class ExecutionLog:
    """
    Records the execution details of a strategy on a task.
    """
    task_id: str
    strategy_name: str
    success: bool
    accuracy: float
    nodes_visited: int
    edges_visited: int
    latency_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert log entry to a dictionary for CSV export."""
        return {
            'task_id': self.task_id,
            'strategy_name': self.strategy_name,
            'success': self.success,
            'accuracy': self.accuracy,
            'nodes_visited': self.nodes_visited,
            'edges_visited': self.edges_visited,
            'latency_ms': self.latency_ms,
            'timestamp': self.timestamp.isoformat(),
            'error_message': self.error_message,
            **self.metadata
        }