from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import json
import numpy as np

@dataclass
class Molecule:
    """
    Data model representing a molecule with its SMILES string,
    optional 3D conformer data, and computed properties.
    
    Attributes:
        smiles (str): Canonical SMILES string.
        mol_id (str): Unique identifier for the molecule.
        molecular_weight (float): Calculated molecular weight.
        sasa (Optional[float]): Solvent Accessible Surface Area (Å²).
        features (Optional[np.ndarray]): Pre-computed molecular features.
        metadata (Dict[str, Any]): Additional metadata.
    """
    smiles: str
    mol_id: str
    molecular_weight: float = 0.0
    sasa: Optional[float] = None
    features: Optional[np.ndarray] = field(default=None)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the Molecule instance to a dictionary."""
        return {
            "smiles": self.smiles,
            "mol_id": self.mol_id,
            "molecular_weight": self.molecular_weight,
            "sasa": self.sasa,
            "metadata": self.metadata
        }

    def to_json(self) -> str:
        """Serialize the Molecule instance to a JSON string."""
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Molecule":
        """Create a Molecule instance from a dictionary."""
        features = data.get("features")
        if isinstance(features, list):
            features = np.array(features)
        return cls(
            smiles=data["smiles"],
            mol_id=data["mol_id"],
            molecular_weight=data.get("molecular_weight", 0.0),
            sasa=data.get("sasa"),
            features=features,
            metadata=data.get("metadata", {})
        )
