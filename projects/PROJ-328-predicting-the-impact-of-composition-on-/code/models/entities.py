"""
Data models and entities for the solder hardness prediction pipeline.

Defines the core domain objects: SolderComposition and CompositionalDescriptor.
These classes serve as the structural backbone for data ingestion, feature engineering,
and model training.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
import json
import math
import logging

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class SolderComposition:
    """
    Represents a single solder alloy composition with its measured properties.
    
    Attributes:
        elemental_breakdown (dict): Dictionary mapping element symbols (str) to 
                                    their weight/atomic percentages (float).
                                    Example: {"Sn": 63.0, "Ag": 3.0, "Cu": 0.9}
        hardness_hv (float): Vickers Hardness value in HV units.
        alloy_family (str): Classification of the alloy family (e.g., "Sn-Ag-Cu", "Pb-Sn").
        source_citation (str): Citation or URL of the source where this data was obtained.
    """
    elemental_breakdown: Dict[str, float]
    hardness_hv: float
    alloy_family: str
    source_citation: str

    def __post_init__(self):
        """Validate the composition after initialization."""
        if not self.elemental_breakdown:
            raise ValueError("elemental_breakdown cannot be empty")
        
        if self.hardness_hv <= 0:
            raise ValueError(f"hardness_hv must be positive, got {self.hardness_hv}")
        
        # Validate that percentages sum to a reasonable value (allowing for some tolerance)
        total = sum(self.elemental_breakdown.values())
        if total < 95.0 or total > 105.0:
            logger.warning(f"Composition sum is {total:.2f}%, which is outside expected range [95, 105]. "
                         f"Source: {self.source_citation}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert the object to a dictionary for serialization."""
        return {
            "elemental_breakdown": self.elemental_breakdown,
            "hardness_hv": self.hardness_hv,
            "alloy_family": self.alloy_family,
            "source_citation": self.source_citation
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SolderComposition':
        """Create an instance from a dictionary."""
        return cls(
            elemental_breakdown=data["elemental_breakdown"],
            hardness_hv=data["hardness_hv"],
            alloy_family=data["alloy_family"],
            source_citation=data["source_citation"]
        )

    def __str__(self) -> str:
        return (f"SolderComposition(family={self.alloy_family}, "
                f"elements={self.elemental_breakdown}, "
                f"HV={self.hardness_hv})")


@dataclass
class CompositionalDescriptor:
    """
    Represents a set of computed physical descriptors for a solder composition.
    
    These descriptors are derived from the elemental composition and elemental
    property databases (e.g., mendeleev) to serve as features for machine learning.
    
    Attributes:
        weighted_mean_atomic_mass (float): Weighted average of atomic masses of constituent elements.
        electronegativity_variance (float): Variance of electronegativity values in the alloy.
        atomic_radius_variance (float): Variance of atomic radii values in the alloy.
        weighted_avg_melting_point (float): Weighted average melting point of constituent elements.
        valence_electron_concentration (float): Average valence electron concentration (VEC).
    """
    weighted_mean_atomic_mass: float
    electronegativity_variance: float
    atomic_radius_variance: float
    weighted_avg_melting_point: float
    valence_electron_concentration: float

    def to_dict(self) -> Dict[str, float]:
        """Convert the object to a dictionary for serialization."""
        return {
            "weighted_mean_atomic_mass": self.weighted_mean_atomic_mass,
            "electronegativity_variance": self.electronegativity_variance,
            "atomic_radius_variance": self.atomic_radius_variance,
            "weighted_avg_melting_point": self.weighted_avg_melting_point,
            "valence_electron_concentration": self.valence_electron_concentration
        }

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'CompositionalDescriptor':
        """Create an instance from a dictionary."""
        return cls(
            weighted_mean_atomic_mass=data["weighted_mean_atomic_mass"],
            electronegativity_variance=data["electronegativity_variance"],
            atomic_radius_variance=data["atomic_radius_variance"],
            weighted_avg_melting_point=data["weighted_avg_melting_point"],
            valence_electron_concentration=data["valence_electron_concentration"]
        )

    def __str__(self) -> str:
        return (f"CompositionalDescriptor(Mass={self.weighted_mean_atomic_mass:.2f}, "
                f"EN_Var={self.electronegativity_variance:.4f}, "
                f"Radius_Var={self.atomic_radius_variance:.4f}, "
                f"Melt={self.weighted_avg_melting_point:.2f}, "
                f"VEC={self.valence_electron_concentration:.2f})")


def create_composition_from_dataframe_row(row: Any) -> SolderComposition:
    """
    Factory function to create a SolderComposition instance from a pandas DataFrame row.
    
    Args:
        row: A pandas Series or dictionary-like object containing the row data.
             Expected keys: 'elemental_breakdown' (dict), 'hardness_hv' (float),
             'alloy_family' (str), 'source_citation' (str).
             
    Returns:
        SolderComposition: An instantiated object.
    """
    try:
        # Handle potential JSON string in 'elemental_breakdown' if loaded from CSV
        elem_data = row.get("elemental_breakdown")
        if isinstance(elem_data, str):
            elem_data = json.loads(elem_data)
        
        return SolderComposition(
            elemental_breakdown=elem_data,
            hardness_hv=float(row["hardness_hv"]),
            alloy_family=str(row["alloy_family"]),
            source_citation=str(row["source_citation"])
        )
    except (KeyError, TypeError, ValueError) as e:
        logger.error(f"Failed to create SolderComposition from row: {row}. Error: {e}")
        raise


def create_descriptor_from_composition(composition: SolderComposition) -> CompositionalDescriptor:
    """
    Factory function to create a CompositionalDescriptor.
    
    Note: This function currently serves as a placeholder for the descriptor engine logic.
    The actual calculation of weighted means and variances based on elemental properties
    is performed by the DescriptorEngine in code/features/descriptor_engine.py.
    This function is provided to satisfy the entity definition requirement.
    
    Args:
        composition: A SolderComposition instance.
        
    Returns:
        CompositionalDescriptor: An instance with zeroed values (to be populated by the engine).
    """
    # In a real pipeline, this would call the DescriptorEngine.
    # For the entity definition, we return a default instance.
    # The actual values are computed in descriptor_engine.py.
    return CompositionalDescriptor(
        weighted_mean_atomic_mass=0.0,
        electronegativity_variance=0.0,
        atomic_radius_variance=0.0,
        weighted_avg_melting_point=0.0,
        valence_electron_concentration=0.0
    )