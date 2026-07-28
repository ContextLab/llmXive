"""
Data model for a single molecule.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import json
import numpy as np


@dataclass
class Molecule:
    """
    Represents a molecule with its SMILES string and associated metadata.

    Attributes:
        smiles: The SMILES string representation of the molecule.
        molecule_id: Optional unique identifier for the molecule.
        metadata: Dictionary for storing additional molecule-specific data.
    """
    smiles: str
    molecule_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the molecule to a dictionary representation."""
        return {
            "smiles": self.smiles,
            "molecule_id": self.molecule_id,
            "metadata": self.metadata
        }

    def to_json(self) -> str:
        """Serialize the molecule to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Molecule":
        """Create a Molecule instance from a dictionary."""
        return cls(
            smiles=data["smiles"],
            molecule_id=data.get("molecule_id"),
            metadata=data.get("metadata", {})
        )

    @classmethod
    def from_json(cls, json_str: str) -> "Molecule":
        """Create a Molecule instance from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
