"""
Data models and entities for the solder hardness prediction pipeline.

This module defines the core data structures for representing solder compositions
and their derived compositional descriptors.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
import json
import math
import logging
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class SolderComposition:
    """
    Represents a single solder alloy composition with its measured hardness.

    Attributes:
        elemental_breakdown (dict): Mapping of element symbols to their weight percentages.
            Example: {"Sn": 96.5, "Ag": 3.0, "Cu": 0.5}
        hardness_hv (float): Vickers hardness measurement in HV units.
        alloy_family (str): Classification of the alloy family (e.g., "Sn-Ag-Cu", "Pb-Sn").
        source_citation (str): Citation or URL of the source where this data was obtained.
    """
    elemental_breakdown: Dict[str, float]
    hardness_hv: float
    alloy_family: str
    source_citation: str

    def __post_init__(self):
        """Validate the composition after initialization."""
        if not isinstance(self.elemental_breakdown, dict):
            raise TypeError("elemental_breakdown must be a dictionary")
        
        if not isinstance(self.hardness_hv, (int, float)):
            raise TypeError("hardness_hv must be a numeric value")
        
        if self.hardness_hv < 0:
            raise ValueError("hardness_hv cannot be negative")
        
        if not isinstance(self.alloy_family, str) or not self.alloy_family.strip():
            raise ValueError("alloy_family must be a non-empty string")
        
        if not isinstance(self.source_citation, str) or not self.source_citation.strip():
            raise ValueError("source_citation must be a non-empty string")

        # Validate that elemental breakdown values are valid percentages
        for element, value in self.elemental_breakdown.items():
            if not isinstance(value, (int, float)):
                raise TypeError(f"Value for element {element} must be numeric")
            if value < 0:
                raise ValueError(f"Value for element {element} cannot be negative")

    def to_dict(self) -> Dict[str, Any]:
        """Convert the object to a dictionary representation."""
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
        elements = ", ".join([f"{k}={v:.1f}" for k, v in self.elemental_breakdown.items()])
        return f"SolderComposition({elements}, HV={self.hardness_hv:.1f}, family={self.alloy_family})"


@dataclass
class CompositionalDescriptor:
    """
    Represents derived physical descriptors for a solder composition.

    These descriptors are calculated from the elemental composition and
    are used as features in machine learning models.

    Attributes:
        weighted_mean_atomic_mass (float): Weighted average of atomic masses.
        electronegativity_variance (float): Variance of electronegativity values.
        atomic_radius_variance (float): Variance of atomic radius values.
        weighted_avg_melting_point (float): Weighted average of melting points.
        valence_electron_concentration (float): Valence electron concentration.
    """
    weighted_mean_atomic_mass: float
    electronegativity_variance: float
    atomic_radius_variance: float
    weighted_avg_melting_point: float
    valence_electron_concentration: float

    def to_dict(self) -> Dict[str, float]:
        """Convert the object to a dictionary representation."""
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
            f"mean_mass={self.weighted_mean_atomic_mass:.2f}, "
            f"en_var={self.electronegativity_variance:.4f}, "
            f"radius_var={self.atomic_radius_variance:.4f}, "
            f"melt={self.weighted_avg_melting_point:.1f}, "
            f"vec={self.valence_electron_concentration:.2f})"
        )


def create_composition_from_dataframe_row(row: Any, source: str = "unknown") -> SolderComposition:
    """
    Create a SolderComposition instance from a pandas DataFrame row.

    Args:
        row: A pandas Series or dictionary-like object containing composition data.
        source: The source citation for this data point.

    Returns:
        A SolderComposition instance.

    Raises:
        ValueError: If required fields are missing or invalid.
    """
    try:
        # Extract elemental breakdown - assuming columns are named with element symbols
        # or in a structured format like "composition_Sn", "composition_Ag", etc.
        elemental_breakdown = {}
        
        # Try to find composition columns
        composition_cols = []
        if hasattr(row, 'keys'):
            keys = list(row.keys())
            composition_cols = [k for k in keys if k.startswith('composition_') or k in ['Sn', 'Ag', 'Cu', 'Pb', 'Bi', 'In', 'Sb', 'Zn', 'Ni', 'Au', 'Ge', 'Ga']]
        
        if composition_cols:
            for col in composition_cols:
                element = col.replace('composition_', '')
                value = row[col]
                if pd.notna(value) and value > 0:
                    elemental_breakdown[element] = float(value)
        
        # If no composition columns found, look for a dict column
        if not elemental_breakdown and 'elemental_breakdown' in row:
            elemental_breakdown = row['elemental_breakdown']
        
        if not elemental_breakdown:
            raise ValueError("No elemental composition data found in row")

        # Extract hardness
        hardness_hv = None
        hardness_cols = ['hardness_hv', 'hardness', 'vickers_hardness', 'HV']
        for col in hardness_cols:
            if col in row and pd.notna(row[col]):
                hardness_hv = float(row[col])
                break
        
        if hardness_hv is None:
            raise ValueError("No hardness value found in row")

        # Extract alloy family
        alloy_family = "Unknown"
        family_cols = ['alloy_family', 'family', 'type']
        for col in family_cols:
            if col in row and pd.notna(row[col]):
                alloy_family = str(row[col])
                break

        return SolderComposition(
            elemental_breakdown=elemental_breakdown,
            hardness_hv=hardness_hv,
            alloy_family=alloy_family,
            source_citation=source
        )
    
    except Exception as e:
        logger.error(f"Failed to create SolderComposition from row: {e}")
        raise


def create_descriptor_from_composition(
    composition: SolderComposition,
    atomic_properties: Dict[str, Dict[str, float]]
) -> CompositionalDescriptor:
    """
    Create a CompositionalDescriptor from a SolderComposition.

    This function calculates physical descriptors based on the elemental
    composition and provided atomic properties.

    Args:
        composition: A SolderComposition instance.
        atomic_properties: A dictionary mapping element symbols to their
            physical properties (atomic_mass, electronegativity, atomic_radius,
            melting_point, valence_electrons).

    Returns:
        A CompositionalDescriptor instance.

    Raises:
        ValueError: If required properties are missing for any element.
    """
    elements = composition.elemental_breakdown
    total_weight = sum(elements.values())
    
    if total_weight == 0:
        raise ValueError("Total composition weight is zero")
    
    # Normalize to fractions
    fractions = {elem: weight / total_weight for elem, weight in elements.items()}
    
    # Initialize accumulators
    weighted_mean_atomic_mass = 0.0
    weighted_mean_en = 0.0
    weighted_mean_radius = 0.0
    weighted_mean_melting_point = 0.0
    weighted_mean_valence = 0.0
    
    # First pass: calculate weighted means
    for elem, fraction in fractions.items():
        if elem not in atomic_properties:
            logger.warning(f"Element {elem} not found in atomic_properties, skipping")
            continue
        
        props = atomic_properties[elem]
        
        weighted_mean_atomic_mass += fraction * props.get('atomic_mass', 0)
        weighted_mean_en += fraction * props.get('electronegativity', 0)
        weighted_mean_radius += fraction * props.get('atomic_radius', 0)
        weighted_mean_melting_point += fraction * props.get('melting_point', 0)
        weighted_mean_valence += fraction * props.get('valence_electrons', 0)
    
    # Second pass: calculate variances
    en_variance = 0.0
    radius_variance = 0.0
    
    for elem, fraction in fractions.items():
        if elem not in atomic_properties:
            continue
        
        props = atomic_properties[elem]
        en = props.get('electronegativity', 0)
        radius = props.get('atomic_radius', 0)
        
        en_variance += fraction * (en - weighted_mean_en) ** 2
        radius_variance += fraction * (radius - weighted_mean_radius) ** 2
    
    return CompositionalDescriptor(
        weighted_mean_atomic_mass=weighted_mean_atomic_mass,
        electronegativity_variance=en_variance,
        atomic_radius_variance=radius_variance,
        weighted_avg_melting_point=weighted_mean_melting_point,
        valence_electron_concentration=weighted_mean_valence
    )


# Import pandas here to avoid circular imports if this module is used in ingestion
try:
    import pandas as pd
except ImportError:
    # Define a minimal mock if pandas is not available (for type checking only)
    class pd:
        @staticmethod
        def notna(value):
            return value is not None