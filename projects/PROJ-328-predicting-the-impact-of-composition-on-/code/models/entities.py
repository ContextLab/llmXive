"""
Core data entities for the solder hardness prediction pipeline.

This module defines the base data models used throughout the project:
- SolderComposition: Represents a single solder alloy with its elemental makeup.
- CompositionalDescriptor: Represents derived features computed from a composition.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from decimal import Decimal
import json
import math

@dataclass
class SolderComposition:
    """
    Represents a single solder alloy composition.

    Attributes:
        alloy_id: Unique identifier for the alloy entry.
        elements: Dictionary mapping element symbols to their weight percentages.
                  The sum of values should be approximately 1.0 (or 100%).
        hardness_hv: Vickers Hardness value in HV units.
        source: Citation or source identifier for this data point.
        temperature_c: Measurement temperature in Celsius (default 25).
        notes: Optional free-text notes about the sample.
    """
    alloy_id: str
    elements: Dict[str, float]
    hardness_hv: Optional[float] = None
    source: Optional[str] = None
    temperature_c: float = 25.0
    notes: Optional[str] = None

    def __post_init__(self):
        """Validate the composition after initialization."""
        if not self.elements:
            raise ValueError("SolderComposition must have at least one element.")
        
        total = sum(self.elements.values())
        if total == 0:
            raise ValueError("Element weights cannot sum to zero.")
        
        # Normalize if not already close to 1.0 (allowing for small floating point errors)
        # We don't auto-normalize in the dataclass to keep raw data integrity,
        # but we flag if it's significantly off.
        if total > 1.1 or total < 0.9:
            # This is a soft warning logic, not an error, as raw data might be in % (0-100)
            # We assume the cleaner module handles unit standardization.
            pass

    def to_dict(self) -> Dict[str, Any]:
        """Convert the object to a dictionary for serialization."""
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
        """Create a SolderComposition from a dictionary."""
        return cls(
            alloy_id=data["alloy_id"],
            elements=data["elements"],
            hardness_hv=data.get("hardness_hv"),
            source=data.get("source"),
            temperature_c=data.get("temperature_c", 25.0),
            notes=data.get("notes")
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "SolderComposition":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))

@dataclass
class CompositionalDescriptor:
    """
    Represents a set of computed descriptors for a solder composition.

    These descriptors are derived from the raw elemental composition using
    physicochemical properties (atomic mass, electronegativity, etc.).

    Attributes:
        alloy_id: Reference to the source SolderComposition.
        clr_vector: The Centered Log-Ratio transformed vector of the composition.
        descriptors: Dictionary of computed scalar descriptors (e.g., weighted mean atomic mass).
        raw_elements: The original elemental composition (for reference).
    """
    alloy_id: str
    clr_vector: List[float]
    descriptors: Dict[str, float]
    raw_elements: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        """Validate the descriptor data."""
        if not self.clr_vector:
            raise ValueError("CLR vector cannot be empty.")
        if not self.descriptors:
            raise ValueError("Descriptor map cannot be empty.")

    def to_dict(self) -> Dict[str, Any]:
        """Convert the object to a dictionary for serialization."""
        return {
            "alloy_id": self.alloy_id,
            "clr_vector": self.clr_vector,
            "descriptors": self.descriptors,
            "raw_elements": self.raw_elements
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompositionalDescriptor":
        """Create a CompositionalDescriptor from a dictionary."""
        return cls(
            alloy_id=data["alloy_id"],
            clr_vector=data["clr_vector"],
            descriptors=data["descriptors"],
            raw_elements=data.get("raw_elements", {})
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "CompositionalDescriptor":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))