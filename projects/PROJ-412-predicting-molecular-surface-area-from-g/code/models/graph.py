"""
Graph data model.
Represents a molecular graph with node and edge features.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import numpy as np

@dataclass
class Graph:
    """
    Data model for a molecular graph representation.
    
    Attributes:
        node_features: N_nodes x D_node_features numpy array.
        edge_index: 2 x N_edges numpy array (source, target).
        edge_features: N_edges x D_edge_features numpy array (optional).
        smiles: Original SMILES string.
        molecular_weight: Molecular weight for the molecule.
        surface_area: Target surface area (optional).
        metadata: Additional metadata dictionary.
    """
    node_features: np.ndarray
    edge_index: np.ndarray
    edge_features: Optional[np.ndarray] = None
    smiles: Optional[str] = None
    molecular_weight: Optional[float] = None
    surface_area: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary representation."""
        return {
            "node_features": self.node_features.tolist(),
            "edge_index": self.edge_index.tolist(),
            "edge_features": self.edge_features.tolist() if self.edge_features is not None else None,
            "smiles": self.smiles,
            "molecular_weight": self.molecular_weight,
            "surface_area": self.surface_area,
            "metadata": self.metadata
        }

    def to_json(self) -> str:
        """Convert graph to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Graph":
        """Create Graph from dictionary."""
        return cls(
            node_features=np.array(data["node_features"]),
            edge_index=np.array(data["edge_index"]),
            edge_features=np.array(data["edge_features"]) if data.get("edge_features") is not None else None,
            smiles=data.get("smiles"),
            molecular_weight=data.get("molecular_weight"),
            surface_area=data.get("surface_area"),
            metadata=data.get("metadata", {})
        )

    @classmethod
    def from_json(cls, json_str: str) -> "Graph":
        """Create Graph from JSON string."""
        return cls.from_dict(json.loads(json_str))
