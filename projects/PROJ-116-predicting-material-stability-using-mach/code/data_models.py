from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
import numpy as np
import json

@dataclass
class MaterialEntry:
    """Data model for a material entry."""
    material_id: str
    composition: Union[str, Dict[str, float]]
    structure: Any  # pymatgen Structure or string representation
    formation_energy_per_atom: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "material_id": self.material_id,
            "composition": self.composition,
            "structure": str(self.structure) if hasattr(self.structure, '__str__') else self.structure,
            "formation_energy_per_atom": self.formation_energy_per_atom,
            "metadata": self.metadata
        }

@dataclass
class FeatureVector:
    """Data model for a feature vector associated with a material."""
    material_id: str
    features: Dict[str, float]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_numpy(self) -> np.ndarray:
        return np.array(list(self.features.values()))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "material_id": self.material_id,
            "features": self.features,
            "metadata": self.metadata
        }
