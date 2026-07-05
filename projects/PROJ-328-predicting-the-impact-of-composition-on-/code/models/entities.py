"""
Core data entities for solder composition and derived descriptors.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from decimal import Decimal
import json

@dataclass
class SolderComposition:
    """
    Represents a single solder alloy composition with elemental breakdown.
    
    Attributes:
        alloy_id: Unique identifier for the alloy sample.
        elements: Dictionary mapping element symbols to their weight percentages.
        hardness_hv: Vickers hardness value (HV).
        source: Citation or source of the data point.
        temperature_c: Measurement temperature in Celsius (default 25).
        notes: Optional notes about the sample or measurement.
    """
    alloy_id: str
    elements: Dict[str, float]
    hardness_hv: float
    source: str
    temperature_c: float = 25.0
    notes: Optional[str] = None

    def __post_init__(self):
        """Validate that composition sums to approximately 100%."""
        total = sum(self.elements.values())
        if not (95.0 <= total <= 105.0):
            raise ValueError(
                f"Elemental composition for {self.alloy_id} sums to {total:.2f}%, "
                "expected ~100%."
            )
        if self.hardness_hv <= 0:
            raise ValueError(
                f"Hardness value for {self.alloy_id} must be positive."
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "alloy_id": self.alloy_id,
            "elements": self.elements,
            "hardness_hv": self.hardness_hv,
            "source": self.source,
            "temperature_c": self.temperature_c,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SolderComposition":
        """Create instance from dictionary."""
        return cls(
            alloy_id=data["alloy_id"],
            elements=data["elements"],
            hardness_hv=data["hardness_hv"],
            source=data["source"],
            temperature_c=data.get("temperature_c", 25.0),
            notes=data.get("notes")
        )

@dataclass
class CompositionalDescriptor:
    """
    Represents engineered features derived from a solder composition.
    
    Attributes:
        alloy_id: Reference to the source alloy.
        clr_coefficients: Centered Log-Ratio transformed coefficients.
        weighted_mean_atomic_mass: Weighted average of atomic masses.
        electronegativity_variance: Variance of electronegativity weighted by composition.
        atomic_radius_variance: Variance of atomic radii weighted by composition.
        weighted_avg_melting_point: Weighted average melting point.
        valence_electron_concentration: Valence electron concentration.
        raw_properties: Dictionary of raw property values used for calculation.
    """
    alloy_id: str
    clr_coefficients: List[float]
    weighted_mean_atomic_mass: float
    electronegativity_variance: float
    atomic_radius_variance: float
    weighted_avg_melting_point: float
    valence_electron_concentration: float
    raw_properties: Dict[str, Dict[str, float]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "alloy_id": self.alloy_id,
            "clr_coefficients": self.clr_coefficients,
            "weighted_mean_atomic_mass": self.weighted_mean_atomic_mass,
            "electronegativity_variance": self.electronegativity_variance,
            "atomic_radius_variance": self.atomic_radius_variance,
            "weighted_avg_melting_point": self.weighted_avg_melting_point,
            "valence_electron_concentration": self.valence_electron_concentration,
            "raw_properties": self.raw_properties
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompositionalDescriptor":
        """Create instance from dictionary."""
        return cls(
            alloy_id=data["alloy_id"],
            clr_coefficients=data["clr_coefficients"],
            weighted_mean_atomic_mass=data["weighted_mean_atomic_mass"],
            electronegativity_variance=data["electronegativity_variance"],
            atomic_radius_variance=data["atomic_radius_variance"],
            weighted_avg_melting_point=data["weighted_avg_melting_point"],
            valence_electron_concentration=data["valence_electron_concentration"],
            raw_properties=data.get("raw_properties", {})
        )