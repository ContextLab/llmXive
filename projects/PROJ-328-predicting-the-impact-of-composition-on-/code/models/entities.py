"""
Core data models/entities for solder alloy composition and derived descriptors.

These dataclasses define the schema for raw composition data and the
engineered features used in the regression models.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
import json
import math
import logging

from seed import set_seed
from utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class SolderComposition:
    """
    Represents a single solder alloy composition with its measured properties.

    Attributes:
        alloy_id: Unique identifier for the alloy record.
        elements: Dictionary mapping element symbol (e.g., 'Sn') to weight fraction (0.0-1.0).
        vickers_hardness: Measured Vickers hardness (HV).
        measurement_temp_c: Temperature at which hardness was measured (°C).
        source_id: Identifier for the data source (e.g., 'NIST-123', 'MP-456').
        notes: Optional free-text notes or caveats.
    """
    alloy_id: str
    elements: Dict[str, float]
    vickers_hardness: Optional[float] = None
    measurement_temp_c: Optional[float] = None
    source_id: Optional[str] = None
    notes: Optional[str] = None

    def __post_init__(self):
        """Validate the composition data upon initialization."""
        if not self.elements:
            raise ValueError(f"SolderComposition {self.alloy_id}: Elements dictionary cannot be empty.")

        # Validate element values are between 0 and 1
        for elem, frac in self.elements.items():
            if not (0.0 <= frac <= 1.0):
                raise ValueError(
                    f"SolderComposition {self.alloy_id}: Element {elem} fraction {frac} "
                    "must be between 0.0 and 1.0."
                )

        # Validate sum of fractions is approximately 1.0 (allowing for small floating point errors)
        total = sum(self.elements.values())
        if not (0.95 <= total <= 1.05):
            logger.warning(
                f"SolderComposition {self.alloy_id}: Element fractions sum to {total:.4f}, "
                "which is outside expected range [0.95, 1.05]. Data may be incomplete."
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the object to a dictionary for serialization."""
        return {
            "alloy_id": self.alloy_id,
            "elements": self.elements,
            "vickers_hardness": self.vickers_hardness,
            "measurement_temp_c": self.measurement_temp_c,
            "source_id": self.source_id,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SolderComposition":
        """Create a SolderComposition instance from a dictionary."""
        return cls(
            alloy_id=data.get("alloy_id", ""),
            elements=data.get("elements", {}),
            vickers_hardness=data.get("vickers_hardness"),
            measurement_temp_c=data.get("measurement_temp_c"),
            source_id=data.get("source_id"),
            notes=data.get("notes")
        )


@dataclass
class CompositionalDescriptor:
    """
    Represents engineered features (descriptors) derived from a SolderComposition.

    These descriptors are calculated based on elemental properties (atomic mass,
    electronegativity, etc.) weighted by the composition fractions.

    Attributes:
        alloy_id: Reference to the source alloy.
        weighted_mean_atomic_mass: Weighted average of atomic masses of constituent elements.
        electronegativity_variance: Variance of electronegativity values weighted by composition.
        atomic_radius_variance: Variance of atomic radii values weighted by composition.
        weighted_avg_melting_point: Weighted average melting point of constituent elements.
        valence_electron_concentration: Average valence electron count per atom.
        clr_transformed_features: The vector of descriptors after CLR transformation.
    """
    alloy_id: str
    weighted_mean_atomic_mass: float = 0.0
    electronegativity_variance: float = 0.0
    atomic_radius_variance: float = 0.0
    weighted_avg_melting_point: float = 0.0
    valence_electron_concentration: float = 0.0
    clr_transformed_features: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the object to a dictionary for serialization."""
        return {
            "alloy_id": self.alloy_id,
            "weighted_mean_atomic_mass": self.weighted_mean_atomic_mass,
            "electronegativity_variance": self.electronegativity_variance,
            "atomic_radius_variance": self.atomic_radius_variance,
            "weighted_avg_melting_point": self.weighted_avg_melting_point,
            "valence_electron_concentration": self.valence_electron_concentration,
            "clr_transformed_features": self.clr_transformed_features
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompositionalDescriptor":
        """Create a CompositionalDescriptor instance from a dictionary."""
        return cls(
            alloy_id=data.get("alloy_id", ""),
            weighted_mean_atomic_mass=data.get("weighted_mean_atomic_mass", 0.0),
            electronegativity_variance=data.get("electronegativity_variance", 0.0),
            atomic_radius_variance=data.get("atomic_radius_variance", 0.0),
            weighted_avg_melting_point=data.get("weighted_avg_melting_point", 0.0),
            valence_electron_concentration=data.get("valence_electron_concentration", 0.0),
            clr_transformed_features=data.get("clr_transformed_features")
        )

    def get_feature_vector(self) -> List[float]:
        """
        Returns the raw feature vector before CLR transformation.
        Used for VIF calculation and diagnostic purposes.
        """
        return [
            self.weighted_mean_atomic_mass,
            self.electronegativity_variance,
            self.atomic_radius_variance,
            self.weighted_avg_melting_point,
            self.valence_electron_concentration
        ]