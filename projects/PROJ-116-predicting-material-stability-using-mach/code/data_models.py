"""
Base data models for Material Stability Prediction Pipeline.

Defines core data structures:
- MaterialEntry: Represents a raw material record with composition, structure, and target values.
- FeatureVector: Represents a processed feature matrix row with metadata and computed features.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import numpy as np


@dataclass
class MaterialEntry:
    """
    Represents a single material entry from the dataset (e.g., OQMD).

    Attributes:
        entry_id: Unique identifier for the material (e.g., OQMD ID).
        composition: Chemical formula string (e.g., "Li2O").
        elements: List of elemental symbols present.
        structure: Pymatgen Structure object or string representation (SMILES/CIF).
        formation_energy: Target variable (formation energy per atom in eV).
        energy_above_hull: Distance to convex hull in eV/atom.
        structure_id: Optional external structure ID.
        metadata: Additional key-value pairs for provenance or flags.
    """
    entry_id: str
    composition: str
    elements: List[str]
    structure: Any  # Can be pymatgen Structure or raw string
    formation_energy: float
    energy_above_hull: Optional[float] = None
    structure_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the entry to a dictionary representation."""
        return {
            "entry_id": self.entry_id,
            "composition": self.composition,
            "elements": self.elements,
            "structure": self.structure,
            "formation_energy": self.formation_energy,
            "energy_above_hull": self.energy_above_hull,
            "structure_id": self.structure_id,
            "metadata": self.metadata,
        }


@dataclass
class FeatureVector:
    """
    Represents a processed feature vector for a material.

    Attributes:
        entry_id: Reference to the original MaterialEntry ID.
        features: Numpy array of numerical features (e.g., Magpie, Voronoi stats).
        feature_names: List of strings corresponding to the feature columns.
        is_valid: Boolean flag indicating if all features were successfully computed.
        validation_errors: List of strings describing any computation failures.
    """
    entry_id: str
    features: np.ndarray
    feature_names: List[str]
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Ensure features is a numpy array."""
        if not isinstance(self.features, np.ndarray):
            self.features = np.array(self.features, dtype=float)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the vector to a dictionary (for JSON/CSV export)."""
        return {
            "entry_id": self.entry_id,
            "features": self.features.tolist(),
            "feature_names": self.feature_names,
            "is_valid": self.is_valid,
            "validation_errors": self.validation_errors,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeatureVector":
        """Reconstruct a FeatureVector from a dictionary."""
        return cls(
            entry_id=data["entry_id"],
            features=np.array(data["features"]),
            feature_names=data["feature_names"],
            is_valid=data.get("is_valid", True),
            validation_errors=data.get("validation_errors", []),
        )
