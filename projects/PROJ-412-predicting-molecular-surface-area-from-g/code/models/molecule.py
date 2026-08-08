from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import json
import numpy as np


@dataclass
class Molecule:
    """
    Data model representing a molecule with its SMILES string,
    atom count, and optional 3D conformer data.
    """
    smiles: str
    atom_count: int
    molecular_weight: Optional[float] = None
    node_features: Optional[np.ndarray] = None
    edge_features: Optional[np.ndarray] = None
    surface_area: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the Molecule instance to a dictionary for serialization."""
        return {
            "smiles": self.smiles,
            "atom_count": self.atom_count,
            "molecular_weight": self.molecular_weight,
            "node_features": self.node_features.tolist() if self.node_features is not None else None,
            "edge_features": self.edge_features.tolist() if self.edge_features is not None else None,
            "surface_area": self.surface_area,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Molecule":
        """Create a Molecule instance from a dictionary."""
        node_features = np.array(data["node_features"]) if data.get("node_features") is not None else None
        edge_features = np.array(data["edge_features"]) if data.get("edge_features") is not None else None
        
        return cls(
            smiles=data["smiles"],
            atom_count=data["atom_count"],
            molecular_weight=data.get("molecular_weight"),
            node_features=node_features,
            edge_features=edge_features,
            surface_area=data.get("surface_area"),
            metadata=data.get("metadata", {})
        )

    def to_json(self) -> str:
        """Serialize the Molecule to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "Molecule":
        """Deserialize a Molecule from a JSON string."""
        return cls.from_dict(json.loads(json_str))

    def __post_init__(self):
        if self.atom_count <= 0:
            raise ValueError("Atom count must be positive.")
        if self.smiles and not isinstance(self.smiles, str):
            raise TypeError("SMILES must be a string.")
