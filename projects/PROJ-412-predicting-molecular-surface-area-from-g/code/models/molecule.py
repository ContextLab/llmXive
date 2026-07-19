"""
Molecule data model.
Represents a molecule with its SMILES string, molecular weight, and 3D conformer data.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import json
import numpy as np

@dataclass
class Molecule:
    """
    Data model for a single molecule.
    
    Attributes:
        smiles: SMILES string representation of the molecule.
        molecular_weight: Calculated molecular weight (g/mol).
        surface_area: Solvent-accessible surface area (SASA) in Å².
        conformer_3d: Optional 3D coordinates (N_atoms x 3 numpy array).
        metadata: Additional metadata dictionary.
    """
    smiles: str
    molecular_weight: float
    surface_area: Optional[float] = None
    conformer_3d: Optional[np.ndarray] = field(default=None)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert molecule to dictionary representation."""
        return {
            "smiles": self.smiles,
            "molecular_weight": self.molecular_weight,
            "surface_area": self.surface_area,
            "conformer_3d": self.conformer_3d.tolist() if self.conformer_3d is not None else None,
            "metadata": self.metadata
        }

    def to_json(self) -> str:
        """Convert molecule to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Molecule":
        """Create Molecule from dictionary."""
        conformer = data.get("conformer_3d")
        if conformer is not None:
            conformer = np.array(conformer)
        return cls(
            smiles=data["smiles"],
            molecular_weight=data["molecular_weight"],
            surface_area=data.get("surface_area"),
            conformer_3d=conformer,
            metadata=data.get("metadata", {})
        )

    @classmethod
    def from_json(cls, json_str: str) -> "Molecule":
        """Create Molecule from JSON string."""
        return cls.from_dict(json.loads(json_str))
