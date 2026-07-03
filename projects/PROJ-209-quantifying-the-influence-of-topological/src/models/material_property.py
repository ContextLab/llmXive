"""
MaterialProperty entity definition.

Represents the physical properties associated with a defect entry,
including pristine references and defect-modified values.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import json
import numpy as np


@dataclass
class MaterialProperty:
    """
    Entity representing material properties for a defect entry.

    Attributes:
        entry_id: Foreign key linking to DefectEntry.
        conductivity: Electrical conductivity in S/m.
        elastic_tensor: 6x6 elastic tensor (Voigt notation) as a flat list of 21 values (Pa).
        fracture_energy: Fracture energy in J/m^2.
        pristine_conductivity: Reference conductivity for the pristine material (S/m).
        pristine_young_modulus: Reference Young's modulus for pristine material (Pa).
        pristine_fracture_strength: Reference fracture strength for pristine material (Pa).
        young_modulus: Calculated Young's modulus (Pa).
        fracture_strength: Calculated fracture strength (Pa).
    """
    entry_id: str
    conductivity: float
    elastic_tensor: List[float]
    fracture_energy: float
    pristine_conductivity: Optional[float] = None
    pristine_young_modulus: Optional[float] = None
    pristine_fracture_strength: Optional[float] = None
    young_modulus: Optional[float] = None
    fracture_strength: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the property to a dictionary."""
        return {
            "entry_id": self.entry_id,
            "conductivity": self.conductivity,
            "elastic_tensor": self.elastic_tensor,
            "fracture_energy": self.fracture_energy,
            "pristine_conductivity": self.pristine_conductivity,
            "pristine_young_modulus": self.pristine_young_modulus,
            "pristine_fracture_strength": self.pristine_fracture_strength,
            "young_modulus": self.young_modulus,
            "fracture_strength": self.fracture_strength
        }

    def to_json(self) -> str:
        """Serialize the property to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MaterialProperty':
        """Create a MaterialProperty from a dictionary."""
        elastic_tensor = data.get("elastic_tensor")
        if isinstance(elastic_tensor, str):
            # Handle JSON stringified list if necessary
            elastic_tensor = json.loads(elastic_tensor)
        
        return cls(
            entry_id=data["entry_id"],
            conductivity=float(data["conductivity"]),
            elastic_tensor=[float(x) for x in elastic_tensor],
            fracture_energy=float(data["fracture_energy"]),
            pristine_conductivity=float(data["pristine_conductivity"]) if data.get("pristine_conductivity") else None,
            pristine_young_modulus=float(data["pristine_young_modulus"]) if data.get("pristine_young_modulus") else None,
            pristine_fracture_strength=float(data["pristine_fracture_strength"]) if data.get("pristine_fracture_strength") else None,
            young_modulus=float(data["young_modulus"]) if data.get("young_modulus") else None,
            fracture_strength=float(data["fracture_strength"]) if data.get("fracture_strength") else None
        )

    @classmethod
    def from_row(cls, row: Dict[str, str]) -> 'MaterialProperty':
        """
        Create a MaterialProperty from a CSV row dictionary.
        Handles type coercion and elastic tensor parsing.
        """
        # Elastic tensor is expected to be a comma-separated string or JSON list in the row
        et_str = row.get("elastic_tensor", "[]")
        if isinstance(et_str, str):
            # Try to parse as JSON list first, then comma-separated
            try:
                et = json.loads(et_str)
            except json.JSONDecodeError:
                et = [float(x.strip()) for x in et_str.split(",") if x.strip()]
        else:
            et = list(et_str)

        return cls(
            entry_id=row["entry_id"],
            conductivity=float(row["conductivity"]),
            elastic_tensor=[float(x) for x in et],
            fracture_energy=float(row["fracture_energy"]),
            pristine_conductivity=float(row["pristine_conductivity"]) if row.get("pristine_conductivity") else None,
            pristine_young_modulus=float(row["pristine_young_modulus"]) if row.get("pristine_young_modulus") else None,
            pristine_fracture_strength=float(row["pristine_fracture_strength"]) if row.get("pristine_fracture_strength") else None,
            young_modulus=float(row["young_modulus"]) if row.get("young_modulus") else None,
            fracture_strength=float(row["fracture_strength"]) if row.get("fracture_strength") else None
        )

    def validate(self) -> bool:
        """
        Validate the physical consistency of the properties.
        Returns True if valid, False otherwise.
        """
        if self.conductivity <= 0:
            return False
        if self.fracture_energy <= 0:
            return False
        if self.elastic_tensor and any(x <= 0 for x in self.elastic_tensor):
            # Basic check; full tensor positivity is more complex
            pass 
        return True
