from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
import numpy as np
import json

@dataclass
class MaterialEntry:
    """Represents a single material entry from a dataset."""
    composition: str
    formation_energy_per_atom: float
    structure: Optional[Any] = None  # pymatgen Structure object
    entry_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "composition": self.composition,
            "formation_energy_per_atom": self.formation_energy_per_atom,
            "entry_id": self.entry_id,
            "metadata": self.metadata
        }

@dataclass
class FeatureVector:
    """Represents a feature vector associated with a material."""
    features: Dict[str, float]
    material_id: Optional[str] = None
    source: str = "magpie"  # e.g., magpie, voronoi, combined

    def to_array(self) -> np.ndarray:
        return np.array(list(self.features.values()))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "features": self.features,
            "material_id": self.material_id,
            "source": self.source
        }
