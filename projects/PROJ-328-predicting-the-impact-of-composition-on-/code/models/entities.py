"""
Base data models and entities for the solder hardness prediction pipeline.

This module defines the core data structures for representing solder alloy
compositions and their derived compositional descriptors.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from decimal import Decimal
import json
import math
import logging

from utils.error_handlers import DataValidationError

logger = logging.getLogger(__name__)


@dataclass
class SolderComposition:
    """
    Represents a single solder alloy composition with its elemental breakdown.

    Attributes:
        alloy_id: Unique identifier for the alloy sample.
        elements: Dictionary mapping element symbols to their weight fractions (0.0 to 1.0).
        vickers_hardness: Measured Vickers hardness (HV) value.
        source: Citation or source identifier for the data point.
        temperature_c: Measurement temperature in Celsius (default 25.0 for room temp).
        notes: Optional free-text notes about the measurement or sample.
    """
    alloy_id: str
    elements: Dict[str, float]
    vickers_hardness: Optional[float] = None
    source: Optional[str] = None
    temperature_c: float = 25.0
    notes: Optional[str] = None

    def __post_init__(self):
        """Validate the composition data after initialization."""
        self._validate_elements()
        self._validate_hardness()

    def _validate_elements(self) -> None:
        """Ensure elements are valid and sum to approximately 1.0."""
        if not self.elements:
            raise DataValidationError(f"Alloy {self.alloy_id}: Elements dictionary cannot be empty.")

        total = sum(self.elements.values())
        # Allow small floating point drift
        if total == 0.0:
            raise DataValidationError(f"Alloy {self.alloy_id}: Sum of element weights is 0.0.")

        # Validation against threshold is usually done in cleaner.py, but we check for basic sanity here
        # We don't enforce the exact 0.95 threshold here as raw data might be unnormalized,
        # but we ensure it's not garbage.
        if total > 1.5 or total < 0.5:
            logger.warning(f"Alloy {self.alloy_id}: Element sum is {total:.4f}, expected ~1.0. "
                           "This might be unnormalized or percentage-based data.")

        for elem, weight in self.elements.items():
            if weight < 0.0 or weight > 1.5:
                raise DataValidationError(
                    f"Alloy {self.alloy_id}: Element {elem} has invalid weight {weight}. "
                    "Weights must be between 0.0 and 1.5 (allowing for >100% due to raw data issues)."
                )

    def _validate_hardness(self) -> None:
        """Ensure hardness is non-negative if present."""
        if self.vickers_hardness is not None and self.vickers_hardness < 0:
            raise DataValidationError(
                f"Alloy {self.alloy_id}: Vickers hardness cannot be negative. "
                f"Got {self.vickers_hardness}."
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the object to a dictionary for serialization."""
        return {
            "alloy_id": self.alloy_id,
            "elements": self.elements,
            "vickers_hardness": self.vickers_hardness,
            "source": self.source,
            "temperature_c": self.temperature_c,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SolderComposition":
        """Create a SolderComposition instance from a dictionary."""
        return cls(
            alloy_id=data["alloy_id"],
            elements=data["elements"],
            vickers_hardness=data.get("vickers_hardness"),
            source=data.get("source"),
            temperature_c=data.get("temperature_c", 25.0),
            notes=data.get("notes")
        )

    def to_json(self) -> str:
        """Serialize the object to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "SolderComposition":
        """Deserialize a SolderComposition from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class CompositionalDescriptor:
    """
    Represents a set of engineered descriptors derived from a solder composition.

    These descriptors are used as features for machine learning models.
    They are calculated based on the raw composition and elemental properties.

    Attributes:
        alloy_id: Reference to the source alloy.
        clr_coefficients: Coefficients from the Centered Log-Ratio (CLR) transform.
        descriptors: Dictionary of calculated feature values (e.g., weighted mean atomic mass).
        raw_elements: The original composition used to derive these descriptors.
    """
    alloy_id: str
    clr_coefficients: Dict[str, float]
    descriptors: Dict[str, float]
    raw_elements: Dict[str, float]

    def __post_init__(self):
        """Validate descriptor data."""
        if not self.descriptors:
            raise DataValidationError(f"Descriptor for {self.alloy_id}: Descriptors dictionary cannot be empty.")
        
        if not self.clr_coefficients:
            raise DataValidationError(f"Descriptor for {self.alloy_id}: CLR coefficients cannot be empty.")

        # Ensure keys match between clr_coefficients and raw_elements (they should represent the same elements)
        if set(self.clr_coefficients.keys()) != set(self.raw_elements.keys()):
            logger.warning(
                f"Descriptor for {self.alloy_id}: Keys in clr_coefficients and raw_elements do not match. "
                "This might indicate a transformation error."
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the object to a dictionary for serialization."""
        return {
            "alloy_id": self.alloy_id,
            "clr_coefficients": self.clr_coefficients,
            "descriptors": self.descriptors,
            "raw_elements": self.raw_elements
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompositionalDescriptor":
        """Create a CompositionalDescriptor instance from a dictionary."""
        return cls(
            alloy_id=data["alloy_id"],
            clr_coefficients=data["clr_coefficients"],
            descriptors=data["descriptors"],
            raw_elements=data["raw_elements"]
        )

    def to_json(self) -> str:
        """Serialize the object to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "CompositionalDescriptor":
        """Deserialize a CompositionalDescriptor from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def get_feature_vector(self, feature_names: Optional[List[str]] = None) -> List[float]:
        """
        Extract the descriptor values as a list of floats for model input.

        Args:
            feature_names: Optional list of specific feature names to include.
                           If None, returns all descriptor values.

        Returns:
            List of float values corresponding to the requested features.
        """
        if feature_names is None:
            feature_names = list(self.descriptors.keys())
        
        return [self.descriptors[name] for name in feature_names]

# Re-export for convenience if imported directly from models
__all__ = ["SolderComposition", "CompositionalDescriptor"]