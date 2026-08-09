from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

class BoundaryType(Enum):
    SYMMETRIC_TILT = "symmetric_tilt"
    ASYMMETRIC_TILT = "asymmetric_tilt"
    twist = "twist"
    GENERIC = "generic"

@dataclass
class SegregationProfile:
    """
    Represents the segregation profile of a solute at a grain boundary.
    """
    system_name: str
    base_element: str
    solutes: List[str]
    boundary_type: BoundaryType
    temperature_K: float
    segregation_energy_eV: float
    bulk_composition: Dict[str, float]
    equilibrium_concentrations: Dict[str, List[float]]
    profile_data: List[Dict[str, Any]] # List of {site_index, concentration, energy}
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "system_name": self.system_name,
            "base_element": self.base_element,
            "solutes": self.solutes,
            "boundary_type": self.boundary_type.value,
            "temperature_K": self.temperature_K,
            "segregation_energy_eV": self.segregation_energy_eV,
            "bulk_composition": self.bulk_composition,
            "equilibrium_concentrations": self.equilibrium_concentrations,
            "profile_data": self.profile_data,
            "metadata": self.metadata
        }
