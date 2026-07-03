"""
DefectEntry entity definition.

Represents a single defect record containing structural, geometric, and
synthesis metadata required for downstream modeling.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import json


@dataclass
class DefectEntry:
    """
    Entity representing a defect entry in the dataset.

    Attributes:
        entry_id: Unique identifier for the entry.
        material_id: Identifier for the base material (e.g., graphene, MoS2).
        structure_id: Identifier for the specific structure configuration.
        defect_type: Type of defect (e.g., 'vacancy', 'substitution', 'grain_boundary').
        defect_density: Density of the defect (dimensionless, 0.0 to 1.0).
        synthesis_method: Method used to create the defect (e.g., 'DFTB+', 'MD').
        grain_size: Average grain size in Angstroms (optional).
        temperature: Temperature during synthesis in Kelvin (optional).
        data_source: Source of the data ('mp', '2022_supplement', 'synthetic').
        metadata: Additional free-form metadata.
    """
    entry_id: str
    material_id: str
    structure_id: str
    defect_type: str
    defect_density: float
    synthesis_method: Optional[str] = None
    grain_size: Optional[float] = None
    temperature: Optional[float] = None
    data_source: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the entry to a dictionary."""
        return {
            "entry_id": self.entry_id,
            "material_id": self.material_id,
            "structure_id": self.structure_id,
            "defect_type": self.defect_type,
            "defect_density": self.defect_density,
            "synthesis_method": self.synthesis_method,
            "grain_size": self.grain_size,
            "temperature": self.temperature,
            "data_source": self.data_source,
            "metadata": self.metadata
        }

    def to_json(self) -> str:
        """Serialize the entry to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DefectEntry':
        """Create a DefectEntry from a dictionary."""
        return cls(
            entry_id=data["entry_id"],
            material_id=data["material_id"],
            structure_id=data["structure_id"],
            defect_type=data["defect_type"],
            defect_density=data["defect_density"],
            synthesis_method=data.get("synthesis_method"),
            grain_size=data.get("grain_size"),
            temperature=data.get("temperature"),
            data_source=data.get("data_source", "unknown"),
            metadata=data.get("metadata", {})
        )

    @classmethod
    def from_row(cls, row: Dict[str, str]) -> 'DefectEntry':
        """
        Create a DefectEntry from a CSV row dictionary.
        Handles type coercion for numeric fields.
        """
        defect_density = float(row.get("defect_density", 0.0))
        grain_size = float(row["grain_size"]) if row.get("grain_size") else None
        temperature = float(row["temperature"]) if row.get("temperature") else None

        return cls(
            entry_id=row["entry_id"],
            material_id=row["material_id"],
            structure_id=row["structure_id"],
            defect_type=row["defect_type"],
            defect_density=defect_density,
            synthesis_method=row.get("synthesis_method"),
            grain_size=grain_size,
            temperature=temperature,
            data_source=row.get("data_source", "unknown"),
            metadata={}
        )
