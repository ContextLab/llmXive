"""
Data model for graph representation of molecules.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import numpy as np


@dataclass
class Graph:
    """
    Represents a molecular graph suitable for Graph Neural Networks.

    Attributes:
        node_features: N x D tensor/array of node features.
        edge_index: 2 x E tensor/array of edge indices (source, target).
        edge_features: E x F tensor/array of edge features.
        y: Target value (e.g., SASA) for regression tasks.
        metadata: Optional metadata dictionary.
    """
    node_features: np.ndarray
    edge_index: np.ndarray
    edge_features: np.ndarray
    y: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the graph to a dictionary."""
        return {
            "node_features": self.node_features.tolist(),
            "edge_index": self.edge_index.tolist(),
            "edge_features": self.edge_features.tolist(),
            "y": self.y,
            "metadata": self.metadata
        }

    def to_json(self) -> str:
        """Serialize the graph to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Graph":
        """Reconstruct a Graph instance from a dictionary."""
        return cls(
            node_features=np.array(data["node_features"]),
            edge_index=np.array(data["edge_index"]),
            edge_features=np.array(data["edge_features"]),
            y=data.get("y"),
            metadata=data.get("metadata", {})
        )

    @classmethod
    def from_json(cls, json_str: str) -> "Graph":
        """Reconstruct a Graph instance from a JSON string."""
        return cls.from_dict(json.loads(json_str))
