from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
import numpy as np
import json

@dataclass
class MaterialEntry:
    """
    Represents a material entry with its composition, structure, and target property.
    """
    material_id: str
    composition: str
    structure_data: Optional[Dict[str, Any]] = None  # Serialized structure (e.g., CIF string or dict)
    formation_energy_per_atom: Optional[float] = None
    energy_above_hull: Optional[float] = None
    elements: List[str] = field(default_factory=list)
    num_elements: int = 0
    num_sites: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "material_id": self.material_id,
            "composition": self.composition,
            "structure_data": self.structure_data,
            "formation_energy_per_atom": self.formation_energy_per_atom,
            "energy_above_hull": self.energy_above_hull,
            "elements": self.elements,
            "num_elements": self.num_elements,
            "num_sites": self.num_sites
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MaterialEntry":
        return cls(
            material_id=data["material_id"],
            composition=data["composition"],
            structure_data=data.get("structure_data"),
            formation_energy_per_atom=data.get("formation_energy_per_atom"),
            energy_above_hull=data.get("energy_above_hull"),
            elements=data.get("elements", []),
            num_elements=data.get("num_elements", 0),
            num_sites=data.get("num_sites", 0)
        )


@dataclass
class FeatureVector:
    """
    Represents a feature vector for a material, containing both compositional
    and local coordination features.
    """
    material_id: str
    magpie_features: Optional[np.ndarray] = None
    voronoi_features: Optional[np.ndarray] = None
    bond_length_features: Optional[np.ndarray] = None
    combined_features: Optional[np.ndarray] = None
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "material_id": self.material_id,
            "magpie_features": self.magpie_features.tolist() if self.magpie_features is not None else None,
            "voronoi_features": self.voronoi_features.tolist() if self.voronoi_features is not None else None,
            "bond_length_features": self.bond_length_features.tolist() if self.bond_length_features is not None else None,
            "combined_features": self.combined_features.tolist() if self.combined_features is not None else None,
            "is_valid": self.is_valid,
            "validation_errors": self.validation_errors
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeatureVector":
        return cls(
            material_id=data["material_id"],
            magpie_features=np.array(data["magpie_features"]) if data.get("magpie_features") is not None else None,
            voronoi_features=np.array(data["voronoi_features"]) if data.get("voronoi_features") is not None else None,
            bond_length_features=np.array(data["bond_length_features"]) if data.get("bond_length_features") is not None else None,
            combined_features=np.array(data["combined_features"]) if data.get("combined_features") is not None else None,
            is_valid=data.get("is_valid", True),
            validation_errors=data.get("validation_errors", [])
        )
