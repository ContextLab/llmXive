"""
Data models and entities for the solder hardness prediction pipeline.

This module defines the core data structures for representing solder alloy
compositions and their derived compositional descriptors.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
import json
import math
import logging

logger = logging.getLogger(__name__)

@dataclass
class SolderComposition:
    """
    Represents a single solder alloy composition with its measured properties.
    
    Attributes:
        elemental_breakdown: Dictionary mapping element symbols to their percentage 
                             in the alloy (e.g., {"Sn": 63, "Pb": 37}).
        hardness_hv: Vickers hardness measurement in HV units.
        alloy_family: Classification of the alloy family (e.g., "Sn-Pb", "Sn-Ag-Cu").
        source_citation: Citation or source identifier for this data point.
    """
    elemental_breakdown: Dict[str, float]
    hardness_hv: float
    alloy_family: str
    source_citation: str

    def __post_init__(self):
        """Validate the composition data upon initialization."""
        if not self.elemental_breakdown:
            raise ValueError("elemental_breakdown cannot be empty")
        
        if not isinstance(self.hardness_hv, (int, float)):
            raise TypeError("hardness_hv must be a numeric value")
        
        if self.hardness_hv <= 0:
            raise ValueError("hardness_hv must be positive")
        
        if not self.alloy_family:
            raise ValueError("alloy_family cannot be empty")
        
        if not self.source_citation:
            raise ValueError("source_citation cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        """Convert the composition to a dictionary representation."""
        return {
            "elemental_breakdown": self.elemental_breakdown,
            "hardness_hv": self.hardness_hv,
            "alloy_family": self.alloy_family,
            "source_citation": self.source_citation
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SolderComposition":
        """Create a SolderComposition instance from a dictionary."""
        return cls(
            elemental_breakdown=data["elemental_breakdown"],
            hardness_hv=float(data["hardness_hv"]),
            alloy_family=data["alloy_family"],
            source_citation=data["source_citation"]
        )

    def to_json(self) -> str:
        """Convert the composition to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "SolderComposition":
        """Create a SolderComposition instance from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def get_total_composition(self) -> float:
        """Calculate the sum of all elemental percentages."""
        return sum(self.elemental_breakdown.values())

    def validate_composition_sum(self, threshold: float = 95.0) -> bool:
        """
        Validate that the elemental composition sums to at least the threshold.
        
        Args:
            threshold: Minimum acceptable sum percentage (default 95.0).
        
        Returns:
            True if the sum meets or exceeds the threshold, False otherwise.
        """
        total = self.get_total_composition()
        return total >= threshold

@dataclass
class CompositionalDescriptor:
    """
    Represents derived physical descriptors calculated from a solder composition.
    
    These descriptors are used as features in machine learning models to predict
    hardness based on the alloy's composition.
    
    Attributes:
        weighted_mean_atomic_mass: Mean atomic mass weighted by elemental composition.
        electronegativity_variance: Variance of electronegativity values weighted by composition.
        atomic_radius_variance: Variance of atomic radii weighted by composition.
        weighted_avg_melting_point: Mean melting point weighted by elemental composition.
        valence_electron_concentration: Average valence electron concentration weighted by composition.
    """
    weighted_mean_atomic_mass: float
    electronegativity_variance: float
    atomic_radius_variance: float
    weighted_avg_melting_point: float
    valence_electron_concentration: float

    def to_dict(self) -> Dict[str, float]:
        """Convert the descriptor to a dictionary representation."""
        return {
            "weighted_mean_atomic_mass": self.weighted_mean_atomic_mass,
            "electronegativity_variance": self.electronegativity_variance,
            "atomic_radius_variance": self.atomic_radius_variance,
            "weighted_avg_melting_point": self.weighted_avg_melting_point,
            "valence_electron_concentration": self.valence_electron_concentration
        }

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "CompositionalDescriptor":
        """Create a CompositionalDescriptor instance from a dictionary."""
        return cls(
            weighted_mean_atomic_mass=float(data["weighted_mean_atomic_mass"]),
            electronegativity_variance=float(data["electronegativity_variance"]),
            atomic_radius_variance=float(data["atomic_radius_variance"]),
            weighted_avg_melting_point=float(data["weighted_avg_melting_point"]),
            valence_electron_concentration=float(data["valence_electron_concentration"])
        )

    def to_json(self) -> str:
        """Convert the descriptor to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "CompositionalDescriptor":
        """Create a CompositionalDescriptor instance from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

def create_composition_from_dataframe_row(row: Dict[str, Any], 
                                          composition_columns: List[str],
                                          target_column: str = "hardness_hv",
                                          family_column: str = "alloy_family",
                                          source_column: str = "source_citation") -> SolderComposition:
    """
    Create a SolderComposition object from a dataframe row (or dictionary representation).
    
    Args:
        row: Dictionary representing a row from a dataframe.
        composition_columns: List of column names representing elemental percentages.
        target_column: Name of the column containing hardness values.
        family_column: Name of the column containing alloy family information.
        source_column: Name of the column containing source citation.
    
    Returns:
        A SolderComposition instance.
    """
    elemental_breakdown = {}
    for col in composition_columns:
        if col in row and row[col] is not None:
            try:
                elemental_breakdown[col] = float(row[col])
            except (ValueError, TypeError):
                logger.warning(f"Could not convert {col} to float, skipping")
    
    if not elemental_breakdown:
        raise ValueError("No valid elemental composition found in row")
    
    try:
        hardness = float(row[target_column])
    except (ValueError, TypeError, KeyError):
        raise ValueError(f"Could not convert {target_column} to float")
    
    family = row.get(family_column, "Unknown")
    source = row.get(source_column, "Unknown")
    
    return SolderComposition(
        elemental_breakdown=elemental_breakdown,
        hardness_hv=hardness,
        alloy_family=str(family),
        source_citation=str(source)
    )

def create_descriptor_from_composition(composition: SolderComposition,
                                       atomic_masses: Dict[str, float],
                                       electronegativities: Dict[str, float],
                                       atomic_radii: Dict[str, float],
                                       melting_points: Dict[str, float],
                                       valence_electrons: Dict[str, int]) -> CompositionalDescriptor:
    """
    Create a CompositionalDescriptor by calculating physical properties from a composition.
    
    Args:
        composition: The SolderComposition to analyze.
        atomic_masses: Dictionary mapping element symbols to atomic masses.
        electronegativities: Dictionary mapping element symbols to electronegativity values.
        atomic_radii: Dictionary mapping element symbols to atomic radii.
        melting_points: Dictionary mapping element symbols to melting points (Celsius).
        valence_electrons: Dictionary mapping element symbols to valence electron counts.
    
    Returns:
        A CompositionalDescriptor instance.
    """
    elements = list(composition.elemental_breakdown.keys())
    percentages = [composition.elemental_breakdown[e] for e in elements]
    total_percent = sum(percentages)
    
    if total_percent == 0:
        raise ValueError("Total composition percentage is zero")
    
    # Normalize percentages to fractions
    fractions = [p / total_percent for p in percentages]
    
    # Calculate weighted mean atomic mass
    weighted_mass = sum(fractions[i] * atomic_masses.get(e, 0.0) 
                      for i, e in enumerate(elements))
    
    # Calculate weighted mean electronegativity
    weighted_en = sum(fractions[i] * electronegativities.get(e, 0.0) 
                    for i, e in enumerate(elements))
    
    # Calculate electronegativity variance
    en_variance = sum(fractions[i] * (electronegativities.get(e, 0.0) - weighted_en) ** 2 
                    for i, e in enumerate(elements))
    
    # Calculate weighted mean atomic radius
    weighted_radius = sum(fractions[i] * atomic_radii.get(e, 0.0) 
                        for i, e in enumerate(elements))
    
    # Calculate atomic radius variance
    radius_variance = sum(fractions[i] * (atomic_radii.get(e, 0.0) - weighted_radius) ** 2 
                        for i, e in enumerate(elements))
    
    # Calculate weighted mean melting point
    weighted_mp = sum(fractions[i] * melting_points.get(e, 0.0) 
                    for i, e in enumerate(elements))
    
    # Calculate weighted mean valence electron concentration
    weighted_vec = sum(fractions[i] * valence_electrons.get(e, 0.0) 
                     for i, e in enumerate(elements))
    
    return CompositionalDescriptor(
        weighted_mean_atomic_mass=weighted_mass,
        electronegativity_variance=en_variance,
        atomic_radius_variance=radius_variance,
        weighted_avg_melting_point=weighted_mp,
        valence_electron_concentration=weighted_vec
    )