"""
Data model for molecular representation.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import json
import numpy as np


@dataclass
class Molecule:
    """
    Represents a molecular entity with its core properties.

    Attributes:
        smiles: The SMILES string representation of the molecule.
        molecular_weight: Calculated molecular weight (g/mol).
        node_features: N x D array of node features (atom properties).
        edge_index: 2 x E array representing edge connectivity.
        edge_features: E x F array of edge features (bond properties).
        sasa: Solvent Accessible Surface Area (Å²).
        metadata: Additional arbitrary metadata.
    """
    smiles: str
    molecular_weight: float
    node_features: np.ndarray
    edge_index: np.ndarray
    edge_features: np.ndarray
    sasa: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the molecule instance to a dictionary."""
        return {
            "smiles": self.smiles,
            "molecular_weight": self.molecular_weight,
            "node_features": self.node_features.tolist(),
            "edge_index": self.edge_index.tolist(),
            "edge_features": self.edge_features.tolist(),
            "sasa": self.sasa,
            "metadata": self.metadata
        }

    def to_json(self) -> str:
        """Serialize the molecule to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Molecule":
        """Reconstruct a Molecule instance from a dictionary."""
        return cls(
            smiles=data["smiles"],
            molecular_weight=data["molecular_weight"],
            node_features=np.array(data["node_features"]),
            edge_index=np.array(data["edge_index"]),
            edge_features=np.array(data["edge_features"]),
            sasa=data.get("sasa"),
            metadata=data.get("metadata", {})
        )

    @classmethod
    def from_json(cls, json_str: str) -> "Molecule":
        """Reconstruct a Molecule instance from a JSON string."""
        return cls.from_dict(json.loads(json_str))
