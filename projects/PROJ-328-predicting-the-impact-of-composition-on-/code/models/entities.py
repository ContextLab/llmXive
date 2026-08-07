"""
Base data models and entities for the solder hardness prediction pipeline.

This module defines the core data structures for representing solder compositions
and their derived compositional descriptors.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from decimal import Decimal
import json
import math
import logging

from seed import set_seed

logger = logging.getLogger(__name__)

@dataclass
class SolderComposition:
    """
    Represents a single solder alloy composition with its elemental breakdown
    and measured Vickers hardness.
    
    Attributes:
        alloy_id: Unique identifier for this alloy composition
        elements: Dictionary mapping element symbols to their weight percentages
        hardness_hv: Measured Vickers hardness value
        temperature_c: Measurement temperature in Celsius (default 25.0)
        source: Citation or source identifier for this data point
        notes: Optional notes or comments about the measurement
    """
    alloy_id: str
    elements: Dict[str, float]
    hardness_hv: float
    temperature_c: float = 25.0
    source: str = "unknown"
    notes: Optional[str] = None
    
    def __post_init__(self):
        """Validate the composition after initialization."""
        if not self.alloy_id:
            raise ValueError("alloy_id cannot be empty")
        
        if not self.elements:
            raise ValueError("elements dictionary cannot be empty")
        
        if self.hardness_hv is None or self.hardness_hv < 0:
            raise ValueError("hardness_hv must be a non-negative number")
        
        # Validate element percentages
        total_composition = sum(self.elements.values())
        if total_composition <= 0:
            raise ValueError("Total composition must be positive")
        
        # Log validation info
        logger.debug(f"Initialized SolderComposition {self.alloy_id} with {len(self.elements)} elements, "
                     f"total composition: {total_composition:.4f}, hardness: {self.hardness_hv} HV")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the composition to a dictionary representation."""
        return {
            "alloy_id": self.alloy_id,
            "elements": self.elements,
            "hardness_hv": self.hardness_hv,
            "temperature_c": self.temperature_c,
            "source": self.source,
            "notes": self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SolderComposition":
        """Create a SolderComposition instance from a dictionary."""
        return cls(
            alloy_id=data["alloy_id"],
            elements=data["elements"],
            hardness_hv=data["hardness_hv"],
            temperature_c=data.get("temperature_c", 25.0),
            source=data.get("source", "unknown"),
            notes=data.get("notes")
        )
    
    def to_json(self) -> str:
        """Serialize the composition to a JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "SolderComposition":
        """Deserialize a SolderComposition from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def get_element_count(self) -> int:
        """Return the number of elements in the composition."""
        return len(self.elements)
    
    def get_total_composition(self) -> float:
        """Return the sum of all element percentages."""
        return sum(self.elements.values())
    
    def is_closed(self, threshold: float = 1.0) -> bool:
        """
        Check if the composition is properly closed (sums to ~100% or 1.0).
        
        Args:
            threshold: Acceptable deviation from perfect closure (default 1.0%)
        
        Returns:
            True if the composition is within the threshold, False otherwise.
        """
        total = self.get_total_composition()
        # Assuming percentages sum to 100, check if within threshold
        return abs(total - 100.0) <= threshold or abs(total - 1.0) <= threshold / 100.0


@dataclass
class CompositionalDescriptor:
    """
    Represents a derived descriptor vector for a solder composition.
    
    These descriptors are computed from the elemental composition using
    compositional data analysis techniques (e.g., CLR transformation)
    and elemental property weighting.
    
    Attributes:
        alloy_id: Reference to the source SolderComposition
        clr_weights: Dictionary of CLR transformation weights for each element
        descriptors: Dictionary of computed descriptor values
        descriptor_names: List of descriptor names in the same order as values
    """
    alloy_id: str
    clr_weights: Dict[str, float]
    descriptors: Dict[str, float]
    descriptor_names: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate the descriptor after initialization."""
        if not self.alloy_id:
            raise ValueError("alloy_id cannot be empty")
        
        if not self.clr_weights:
            raise ValueError("clr_weights cannot be empty")
        
        if not self.descriptors:
            raise ValueError("descriptors cannot be empty")
        
        # If descriptor_names provided, validate length matches descriptors
        if self.descriptor_names:
            if len(self.descriptor_names) != len(self.descriptors):
                raise ValueError("descriptor_names length must match descriptors length")
        
        logger.debug(f"Initialized CompositionalDescriptor {self.alloy_id} with {len(self.descriptors)} descriptors")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the descriptor to a dictionary representation."""
        return {
            "alloy_id": self.alloy_id,
            "clr_weights": self.clr_weights,
            "descriptors": self.descriptors,
            "descriptor_names": self.descriptor_names
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompositionalDescriptor":
        """Create a CompositionalDescriptor instance from a dictionary."""
        return cls(
            alloy_id=data["alloy_id"],
            clr_weights=data["clr_weights"],
            descriptors=data["descriptors"],
            descriptor_names=data.get("descriptor_names", [])
        )
    
    def to_json(self) -> str:
        """Serialize the descriptor to a JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "CompositionalDescriptor":
        """Deserialize a CompositionalDescriptor from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def get_descriptor_vector(self) -> List[float]:
        """
        Return the descriptor values as a list.
        
        If descriptor_names are provided, values are ordered accordingly.
        Otherwise, returns values in arbitrary order (dictionary iteration).
        """
        if self.descriptor_names:
            return [self.descriptors[name] for name in self.descriptor_names]
        return list(self.descriptors.values())
    
    def get_descriptor_names(self) -> List[str]:
        """
        Return the list of descriptor names.
        
        If not explicitly set, generates names from descriptor keys.
        """
        if self.descriptor_names:
            return self.descriptor_names
        return list(self.descriptors.keys())
    
    def get_element_count(self) -> int:
        """Return the number of elements used in the CLR weights."""
        return len(self.clr_weights)
    
    def get_descriptor_count(self) -> int:
        """Return the number of descriptors."""
        return len(self.descriptors)