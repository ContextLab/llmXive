"""
Data model for a molecular graph representation.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import numpy as np


@dataclass
class Graph:
    """
    Represents a molecular graph with node and edge features.

    Attributes:
        node_features: 2D numpy array of shape (num_nodes, num_node_features).
        edge_index: 2D numpy array of shape (2, num_edges) containing edge indices.
        edge_features: 2D numpy array of shape (num_edges, num_edge_features).
        molecular_weight: Optional molecular weight of the molecule.
        surface_area: Optional surface area (SASA) value.
        metadata: Dictionary for storing additional graph-specific data.
    """
    node_features: np.ndarray
    edge_index: np.ndarray
    edge_features: Optional[np.ndarray] = None
    molecular_weight: Optional[float] = None
    surface_area: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure numpy arrays are properly typed."""
        if not isinstance(self.node_features, np.ndarray):
            self.node_features = np.array(self.node_features)
        if not isinstance(self.edge_index, np.ndarray):
            self.edge_index = np.array(self.edge_index)
        if self.edge_features is not None and not isinstance(self.edge_features, np.ndarray):
            self.edge_features = np.array(self.edge_features)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the graph to a dictionary representation."""
        return {
            "node_features": self.node_features.tolist(),
            "edge_index": self.edge_index.tolist(),
            "edge_features": self.edge_features.tolist() if self.edge_features is not None else None,
            "molecular_weight": self.molecular_weight,
            "surface_area": self.surface_area,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Graph":
        """Create a Graph instance from a dictionary."""
        return cls(
            node_features=np.array(data["node_features"]),
            edge_index=np.array(data["edge_index"]),
            edge_features=np.array(data["edge_features"]) if data.get("edge_features") is not None else None,
            molecular_weight=data.get("molecular_weight"),
            surface_area=data.get("surface_area"),
            metadata=data.get("metadata", {})
        )
