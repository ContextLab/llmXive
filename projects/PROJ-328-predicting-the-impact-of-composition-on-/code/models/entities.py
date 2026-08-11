"""
Core data entities for solder composition and derived descriptors.

This module defines the fundamental data structures used throughout the pipeline
to represent solder alloys and their calculated compositional descriptors.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
import json
import math
import logging

from utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class SolderComposition:
    """
    Represents a single solder alloy composition with its measured properties.

    Attributes:
        alloy_id: Unique identifier for the alloy record.
        elements: Dictionary mapping element symbols to their weight fractions.
                  Must sum to approximately 1.0 (within tolerance).
        hardness_hv: Measured Vickers Hardness value.
        measurement_temp_c: Temperature at which hardness was measured.
        source_id: Identifier for the data source (e.g., 'nist', 'mp', 'literature').
        raw_metadata: Dictionary for any additional unstructured metadata.
    """
    alloy_id: str
    elements: Dict[str, float]
    hardness_hv: float
    measurement_temp_c: float
    source_id: str
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate the composition upon initialization."""
        if not self.elements:
            raise ValueError("SolderComposition must have at least one element.")

        total = sum(self.elements.values())
        if not (0.95 <= total <= 1.05):
            # Log warning but do not fail here; validation is handled by the pipeline
            logger.warning(
                f"Composition sum for {self.alloy_id} is {total:.4f}, "
                "expected ~1.0. Validation will occur in the pipeline."
            )

        if self.hardness_hv <= 0:
            raise ValueError(f"Hardness must be positive for {self.alloy_id}.")

    @property
    def num_elements(self) -> int:
        """Return the number of distinct elements in the composition."""
        return len(self.elements)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the entity to a dictionary for serialization."""
        return {
            "alloy_id": self.alloy_id,
            "elements": self.elements,
            "hardness_hv": self.hardness_hv,
            "measurement_temp_c": self.measurement_temp_c,
            "source_id": self.source_id,
            "raw_metadata": self.raw_metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SolderComposition':
        """Create an instance from a dictionary."""
        return cls(
            alloy_id=data["alloy_id"],
            elements=data["elements"],
            hardness_hv=data["hardness_hv"],
            measurement_temp_c=data["measurement_temp_c"],
            source_id=data["source_id"],
            raw_metadata=data.get("raw_metadata", {})
        )

    def to_json(self) -> str:
        """Serialize the entity to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'SolderComposition':
        """Deserialize a JSON string to an entity."""
        return cls.from_dict(json.loads(json_str))


@dataclass(frozen=True)
class CompositionalDescriptor:
    """
    Represents a vector of calculated descriptors derived from a solder composition.

    These descriptors are engineered features used as inputs for machine learning models.
    They capture physical and chemical properties of the alloy based on its elemental makeup.

    Attributes:
        alloy_id: Reference to the source SolderComposition.
        weighted_mean_atomic_mass: Weighted average of atomic masses of constituent elements.
        electronegativity_variance: Variance of electronegativity values weighted by composition.
        atomic_radius_variance: Variance of atomic radii values weighted by composition.
        weighted_avg_melting_point: Weighted average of melting points.
        valence_electron_concentration: Average valence electron count weighted by composition.
        clr_transformed: Optional vector of CLR-transformed values if applicable.
        raw_composition: The original composition fractions used for calculation.
        source_id: Reference to the data source.
    """
    alloy_id: str
    weighted_mean_atomic_mass: float
    electronegativity_variance: float
    atomic_radius_variance: float
    weighted_avg_melting_point: float
    valence_electron_concentration: float
    clr_transformed: Optional[Tuple[float, ...]] = None
    raw_composition: Optional[Dict[str, float]] = None
    source_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert the entity to a dictionary for serialization."""
        return {
            "alloy_id": self.alloy_id,
            "weighted_mean_atomic_mass": self.weighted_mean_atomic_mass,
            "electronegativity_variance": self.electronegativity_variance,
            "atomic_radius_variance": self.atomic_radius_variance,
            "weighted_avg_melting_point": self.weighted_avg_melting_point,
            "valence_electron_concentration": self.valence_electron_concentration,
            "clr_transformed": list(self.clr_transformed) if self.clr_transformed else None,
            "raw_composition": self.raw_composition,
            "source_id": self.source_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CompositionalDescriptor':
        """Create an instance from a dictionary."""
        clr = data.get("clr_transformed")
        if clr is not None:
            clr = tuple(clr)
        return cls(
            alloy_id=data["alloy_id"],
            weighted_mean_atomic_mass=data["weighted_mean_atomic_mass"],
            electronegativity_variance=data["electronegativity_variance"],
            atomic_radius_variance=data["atomic_radius_variance"],
            weighted_avg_melting_point=data["weighted_avg_melting_point"],
            valence_electron_concentration=data["valence_electron_concentration"],
            clr_transformed=clr,
            raw_composition=data.get("raw_composition"),
            source_id=data.get("source_id", "")
        )

    def to_json(self) -> str:
        """Serialize the entity to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'CompositionalDescriptor':
        """Deserialize a JSON string to an entity."""
        return cls.from_dict(json.loads(json_str))

    def get_feature_vector(self) -> List[float]:
        """
        Returns the primary feature vector for modeling.
        Order: [mean_mass, elec_var, radius_var, melt_point, valence]
        """
        return [
            self.weighted_mean_atomic_mass,
            self.electronegativity_variance,
            self.atomic_radius_variance,
            self.weighted_avg_melting_point,
            self.valence_electron_concentration
        ]