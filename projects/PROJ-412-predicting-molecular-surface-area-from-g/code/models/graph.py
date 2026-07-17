from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import numpy as np

@dataclass
class Graph:
    """
    Data model representing a molecular graph derived from a Molecule.
    Used for graph neural network inputs.
    
    Attributes:
        node_features (np.ndarray): Matrix of shape (num_nodes, num_node_features).
        edge_index (np.ndarray): Matrix of shape (2, num_edges) for adjacency.
        edge_features (Optional[np.ndarray]): Matrix of shape (num_edges, num_edge_features).
        graph_label (Optional[float]): Target value (e.g., SASA) for the graph.
        mol_id (str): Reference to the source molecule ID.
        metadata (Dict[str, Any]): Additional graph metadata.
    """
    node_features: np.ndarray
    edge_index: np.ndarray
    edge_features: Optional[np.ndarray] = None
    graph_label: Optional[float] = None
    mol_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure numpy arrays are correctly typed."""
        if not isinstance(self.node_features, np.ndarray):
            self.node_features = np.array(self.node_features)
        if not isinstance(self.edge_index, np.ndarray):
            self.edge_index = np.array(self.edge_index)
        if self.edge_features is not None and not isinstance(self.edge_features, np.ndarray):
            self.edge_features = np.array(self.edge_features)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the Graph instance to a dictionary (serializable)."""
        return {
            "node_features": self.node_features.tolist(),
            "edge_index": self.edge_index.tolist(),
            "edge_features": self.edge_features.tolist() if self.edge_features is not None else None,
            "graph_label": self.graph_label,
            "mol_id": self.mol_id,
            "metadata": self.metadata
        }

    def to_json(self) -> str:
        """Serialize the Graph instance to a JSON string."""
        import json
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Graph":
        """Create a Graph instance from a dictionary."""
        return cls(
            node_features=np.array(data["node_features"]),
            edge_index=np.array(data["edge_index"]),
            edge_features=np.array(data["edge_features"]) if data.get("edge_features") is not None else None,
            graph_label=data.get("graph_label"),
            mol_id=data.get("mol_id", ""),
            metadata=data.get("metadata", {})
        )
