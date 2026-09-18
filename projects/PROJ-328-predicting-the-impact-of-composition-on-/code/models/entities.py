"""
Base data models and entities for the solder hardness prediction pipeline.

This module defines the core data structures used throughout the pipeline:
- SolderComposition: Represents a raw solder alloy composition with hardness
- CompositionalDescriptor: Represents computed physical descriptors for ML models
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
import json
import math
import logging

from utils.error_handlers import DataValidationError

logger = logging.getLogger(__name__)

@dataclass
class SolderComposition:
    """
    Represents a single solder alloy composition with its measured Vickers hardness.
    
    Attributes:
        elemental_breakdown: Dictionary mapping element symbols to their weight/atomic percentages.
                           Must sum to approximately 100 (within COMPOSITION_SUM_THRESHOLD).
        hardness_hv: Measured Vickers hardness value in HV units.
        alloy_family: Classification of the alloy family (e.g., "Sn-Ag-Cu", "Pb-Free", "Sn-Pb").
        source_citation: Citation string for the data source (DOI, paper title, etc.).
    """
    elemental_breakdown: Dict[str, float]
    hardness_hv: float
    alloy_family: str
    source_citation: str
    
    def __post_init__(self):
        """Validate the composition after initialization."""
        if not self.elemental_breakdown:
            raise DataValidationError("elemental_breakdown cannot be empty")
        
        if not isinstance(self.hardness_hv, (int, float)):
            raise DataValidationError(f"hardness_hv must be numeric, got {type(self.hardness_hv)}")
        
        if self.hardness_hv <= 0:
            raise DataValidationError(f"hardness_hv must be positive, got {self.hardness_hv}")
        
        if not self.alloy_family or not isinstance(self.alloy_family, str):
            raise DataValidationError("alloy_family must be a non-empty string")
        
        if not self.source_citation or not isinstance(self.source_citation, str):
            raise DataValidationError("source_citation must be a non-empty string")
        
        # Validate composition sum
        total = sum(self.elemental_breakdown.values())
        if total == 0:
            raise DataValidationError("Sum of elemental breakdown cannot be zero")
        
        # Log if sum is significantly off 100 (common in raw data)
        if abs(total - 100.0) > 5.0:
            logger.warning(f"Composition sum is {total:.2f}, expected ~100.0 for source: {self.source_citation}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the composition to a dictionary for serialization."""
        return {
            "elemental_breakdown": self.elemental_breakdown,
            "hardness_hv": self.hardness_hv,
            "alloy_family": self.alloy_family,
            "source_citation": self.source_citation
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SolderComposition':
        """Create a SolderComposition instance from a dictionary."""
        return cls(
            elemental_breakdown=data["elemental_breakdown"],
            hardness_hv=data["hardness_hv"],
            alloy_family=data["alloy_family"],
            source_citation=data["source_citation"]
        )
    
    def __repr__(self) -> str:
        return (
            f"SolderComposition(elements={list(self.elemental_breakdown.keys())}, "
            f"hardness={self.hardness_hv:.2f} HV, family={self.alloy_family})"
        )

@dataclass
class CompositionalDescriptor:
    """
    Represents computed physical descriptors derived from a solder composition.
    
    These descriptors are used as features in machine learning models to predict
    hardness based on composition.
    
    Attributes:
        weighted_mean_atomic_mass: Weighted average of atomic masses of constituent elements.
        electronegativity_variance: Variance of electronegativity values weighted by composition.
        atomic_radius_variance: Variance of atomic radii weighted by composition.
        weighted_avg_melting_point: Weighted average of melting points of constituent elements.
        valence_electron_concentration: Average valence electron concentration weighted by composition.
    """
    weighted_mean_atomic_mass: float
    electronegativity_variance: float
    atomic_radius_variance: float
    weighted_avg_melting_point: float
    valence_electron_concentration: float
    
    def __post_init__(self):
        """Validate descriptor values."""
        for attr_name in [
            "weighted_mean_atomic_mass",
            "electronegativity_variance",
            "atomic_radius_variance",
            "weighted_avg_melting_point",
            "valence_electron_concentration"
        ]:
            value = getattr(self, attr_name)
            if not isinstance(value, (int, float)):
                raise DataValidationError(f"{attr_name} must be numeric, got {type(value)}")
            if math.isnan(value) or math.isinf(value):
                raise DataValidationError(f"{attr_name} cannot be NaN or Inf")
    
    def to_dict(self) -> Dict[str, float]:
        """Convert the descriptor to a dictionary for serialization."""
        return {
            "weighted_mean_atomic_mass": self.weighted_mean_atomic_mass,
            "electronegativity_variance": self.electronegativity_variance,
            "atomic_radius_variance": self.atomic_radius_variance,
            "weighted_avg_melting_point": self.weighted_avg_melting_point,
            "valence_electron_concentration": self.valence_electron_concentration
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'CompositionalDescriptor':
        """Create a CompositionalDescriptor instance from a dictionary."""
        return cls(
            weighted_mean_atomic_mass=data["weighted_mean_atomic_mass"],
            electronegativity_variance=data["electronegativity_variance"],
            atomic_radius_variance=data["atomic_radius_variance"],
            weighted_avg_melting_point=data["weighted_avg_melting_point"],
            valence_electron_concentration=data["valence_electron_concentration"]
        )
    
    def __repr__(self) -> str:
        return (
            f"CompositionalDescriptor("
            f"mass={self.weighted_mean_atomic_mass:.2f}, "
            f"en_var={self.electronegativity_variance:.4f}, "
            f"radius_var={self.atomic_radius_variance:.4f}, "
            f"mp={self.weighted_avg_melting_point:.2f}, "
            f"vec={self.valence_electron_concentration:.4f})"
        )

def create_composition_from_dataframe_row(row: Any) -> SolderComposition:
    """
    Create a SolderComposition instance from a pandas DataFrame row or dict-like object.
    
    Expected row structure:
    - 'elemental_breakdown': dict or JSON string of element percentages
    - 'hardness_hv': float
    - 'alloy_family': str
    - 'source_citation': str
    
    Args:
        row: A dictionary or pandas Series containing composition data.
        
    Returns:
        A validated SolderComposition instance.
        
    Raises:
        DataValidationError: If required fields are missing or invalid.
    """
    try:
        # Handle JSON string for elemental_breakdown if necessary
        elemental_breakdown = row.get("elemental_breakdown")
        if isinstance(elemental_breakdown, str):
            elemental_breakdown = json.loads(elemental_breakdown)
        
        if not isinstance(elemental_breakdown, dict):
            raise DataValidationError("elemental_breakdown must be a dictionary or JSON string")
        
        return SolderComposition(
            elemental_breakdown=elemental_breakdown,
            hardness_hv=float(row["hardness_hv"]),
            alloy_family=str(row["alloy_family"]),
            source_citation=str(row["source_citation"])
        )
    except KeyError as e:
        raise DataValidationError(f"Missing required field in dataframe row: {e}")
    except (ValueError, json.JSONDecodeError) as e:
        raise DataValidationError(f"Invalid data format in dataframe row: {e}")

def create_descriptor_from_composition(
    composition: SolderComposition,
    elemental_properties: Dict[str, Dict[str, float]]
) -> CompositionalDescriptor:
    """
    Compute physical descriptors from a SolderComposition using elemental properties.
    
    Args:
        composition: The SolderComposition instance to process.
        elemental_properties: A dictionary mapping element symbols to their properties:
            {
                "Sn": {"atomic_mass": 118.71, "electronegativity": 1.96, "atomic_radius": 140, "melting_point": 231.9, "valence_electrons": 4},
                ...
            }
            
    Returns:
        A CompositionalDescriptor instance with computed features.
        
    Raises:
        DataValidationError: If required elemental properties are missing.
    """
    elements = list(composition.elemental_breakdown.keys())
    weights = list(composition.elemental_breakdown.values())
    
    # Normalize weights to sum to 1.0
    total_weight = sum(weights)
    if total_weight == 0:
        raise DataValidationError("Cannot compute descriptors with zero total weight")
    
    normalized_weights = [w / total_weight for w in weights]
    
    # Check for missing properties
    required_props = ["atomic_mass", "electronegativity", "atomic_radius", "melting_point", "valence_electrons"]
    for elem in elements:
        if elem not in elemental_properties:
            raise DataValidationError(f"Missing properties for element: {elem}")
        for prop in required_props:
            if prop not in elemental_properties[elem]:
                raise DataValidationError(f"Missing property '{prop}' for element: {elem}")
    
    # Compute weighted mean atomic mass
    weighted_mean_atomic_mass = sum(
        w * elemental_properties[elem]["atomic_mass"]
        for w, elem in zip(normalized_weights, elements)
    )
    
    # Compute weighted mean properties for variance calculation
    means = {}
    for prop in ["electronegativity", "atomic_radius", "melting_point", "valence_electrons"]:
        means[prop] = sum(
            w * elemental_properties[elem][prop]
            for w, elem in zip(normalized_weights, elements)
        )
    
    # Compute variances
    electronegativity_variance = sum(
        w * (elemental_properties[elem]["electronegativity"] - means["electronegativity"]) ** 2
        for w, elem in zip(normalized_weights, elements)
    )
    
    atomic_radius_variance = sum(
        w * (elemental_properties[elem]["atomic_radius"] - means["atomic_radius"]) ** 2
        for w, elem in zip(normalized_weights, elements)
    )
    
    # Weighted average melting point
    weighted_avg_melting_point = means["melting_point"]
    
    # Valence electron concentration (weighted average)
    valence_electron_concentration = means["valence_electrons"]
    
    return CompositionalDescriptor(
        weighted_mean_atomic_mass=weighted_mean_atomic_mass,
        electronegativity_variance=electronegativity_variance,
        atomic_radius_variance=atomic_radius_variance,
        weighted_avg_melting_point=weighted_avg_melting_point,
        valence_electron_concentration=valence_electron_concentration
    )