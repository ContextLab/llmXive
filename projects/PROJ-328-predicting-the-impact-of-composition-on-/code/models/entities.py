"""
Data models and entities for the solder hardness prediction pipeline.

Defines core data structures:
- SolderComposition: Represents a single solder alloy composition with elemental percentages.
- CompositionalDescriptor: Represents derived physical/chemical descriptors for an alloy.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
import json
import math
import logging
import pandas as pd
from pathlib import Path

from utils.error_handlers import CompositionSumError, DataValidationError
from utils.logging_config import get_logger

logger = get_logger(__name__)

@dataclass(frozen=True)
class SolderComposition:
    """
    Immutable data class representing a solder alloy composition.

    Attributes:
        alloy_id: Unique identifier for the alloy record.
        source: Original data source (e.g., 'Materials Project', 'NIST', 'Literature').
        elements: Dictionary mapping element symbol to weight percentage.
        hardness_hv: Vickers hardness value in HV units.
        measurement_temp_c: Temperature at which hardness was measured (°C).
        notes: Optional free-text notes or metadata.
    """
    alloy_id: str
    source: str
    elements: Dict[str, float]
    hardness_hv: float
    measurement_temp_c: float
    notes: Optional[str] = None

    def __post_init__(self):
        """Validate composition data after initialization."""
        if not self.elements:
            raise DataValidationError(f"Elements dictionary cannot be empty for alloy {self.alloy_id}")

        total_composition = sum(self.elements.values())
        if total_composition < 95.0 or total_composition > 105.0:
            raise CompositionSumError(
                f"Composition sum for {self.alloy_id} is {total_composition:.2f}%, "
                f"outside valid range [95%, 105%]."
            )

        if self.hardness_hv <= 0:
            raise DataValidationError(
                f"Hardness value for {self.alloy_id} must be positive, got {self.hardness_hv}"
            )

        if self.measurement_temp_c < -273.15:
            raise DataValidationError(
                f"Measurement temperature for {self.alloy_id} cannot be below absolute zero."
            )

    @property
    def num_elements(self) -> int:
        """Return the number of elements in the composition."""
        return len(self.elements)

    def get_element_list(self) -> List[str]:
        """Return a sorted list of element symbols present in the composition."""
        return sorted(self.elements.keys())

    def to_dict(self) -> Dict[str, Any]:
        """Convert the composition to a dictionary for serialization."""
        return {
            'alloy_id': self.alloy_id,
            'source': self.source,
            'elements': self.elements,
            'hardness_hv': self.hardness_hv,
            'measurement_temp_c': self.measurement_temp_c,
            'notes': self.notes
        }

    def to_json(self) -> str:
        """Serialize the composition to a JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SolderComposition':
        """Create a SolderComposition instance from a dictionary."""
        return cls(
            alloy_id=data['alloy_id'],
            source=data['source'],
            elements=data['elements'],
            hardness_hv=data['hardness_hv'],
            measurement_temp_c=data['measurement_temp_c'],
            notes=data.get('notes')
        )

    @classmethod
    def from_dataframe_row(cls, row: pd.Series, source: str = 'unknown') -> 'SolderComposition':
        """
        Create a SolderComposition from a pandas DataFrame row.

        Expected row format:
        - 'alloy_id': str
        - 'hardness_hv': float
        - 'measurement_temp_c': float
        - Element columns (e.g., 'Sn', 'Ag', 'Cu') with float values
        - Optional 'notes' column
        """
        if 'alloy_id' not in row.index:
            raise DataValidationError("Row must contain 'alloy_id' column")
        if 'hardness_hv' not in row.index:
            raise DataValidationError("Row must contain 'hardness_hv' column")
        if 'measurement_temp_c' not in row.index:
            raise DataValidationError("Row must contain 'measurement_temp_c' column")

        # Identify element columns (assumed to be uppercase letter sequences)
        import re
        element_pattern = re.compile(r'^[A-Z][a-z]?$')
        elements = {}
        for col in row.index:
            if element_pattern.match(str(col)):
                val = float(row[col])
                if val > 0:
                    elements[str(col)] = val

        if not elements:
            raise DataValidationError(f"No valid elemental composition found in row for {row['alloy_id']}")

        notes = row.get('notes', None)

        return cls(
            alloy_id=str(row['alloy_id']),
            source=source,
            elements=elements,
            hardness_hv=float(row['hardness_hv']),
            measurement_temp_c=float(row['measurement_temp_c']),
            notes=notes
        )

@dataclass(frozen=True)
class CompositionalDescriptor:
    """
    Immutable data class representing derived descriptors for a solder alloy.

    These descriptors are computed from the elemental composition and
    physical properties of the constituent elements.

    Attributes:
        alloy_id: Reference to the source SolderComposition.
        weighted_mean_atomic_mass: Weighted average of atomic masses.
        electronegativity_variance: Variance of electronegativity values.
        atomic_radius_variance: Variance of atomic radii.
        weighted_avg_melting_point: Weighted average of melting points.
        valence_electron_concentration: Average valence electron concentration.
        clr_composition: Centered Log-Ratio transformed composition vector.
        element_symbols: Ordered list of elements corresponding to CLR values.
    """
    alloy_id: str
    weighted_mean_atomic_mass: float
    electronegativity_variance: float
    atomic_radius_variance: float
    weighted_avg_melting_point: float
    valence_electron_concentration: float
    clr_composition: Tuple[float, ...]
    element_symbols: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        """Convert the descriptor to a dictionary for serialization."""
        return {
            'alloy_id': self.alloy_id,
            'weighted_mean_atomic_mass': self.weighted_mean_atomic_mass,
            'electronegativity_variance': self.electronegativity_variance,
            'atomic_radius_variance': self.atomic_radius_variance,
            'weighted_avg_melting_point': self.weighted_avg_melting_point,
            'valence_electron_concentration': self.valence_electron_concentration,
            'clr_composition': list(self.clr_composition),
            'element_symbols': list(self.element_symbols)
        }

    def to_feature_vector(self) -> List[float]:
        """
        Return a flat feature vector combining CLR composition and physical descriptors.
        Order: [clr_1, clr_2, ..., clr_n, mean_mass, var_en, var_radius, mean_mp, vec]
        """
        return list(self.clr_composition) + [
            self.weighted_mean_atomic_mass,
            self.electronegativity_variance,
            self.atomic_radius_variance,
            self.weighted_avg_melting_point,
            self.valence_electron_concentration
        ]

    @classmethod
    def from_composition(
        cls,
        composition: SolderComposition,
        clr_values: Tuple[float, ...],
        element_order: List[str],
        mean_atomic_mass: float,
        var_en: float,
        var_radius: float,
        mean_melting_point: float,
        vec: float
    ) -> 'CompositionalDescriptor':
        """Factory method to create a descriptor from a composition and computed values."""
        return cls(
            alloy_id=composition.alloy_id,
            weighted_mean_atomic_mass=mean_atomic_mass,
            electronegativity_variance=var_en,
            atomic_radius_variance=var_radius,
            weighted_avg_melting_point=mean_melting_point,
            valence_electron_concentration=vec,
            clr_composition=clr_values,
            element_symbols=tuple(element_order)
        )

def create_composition_from_dataframe_row(
    row: pd.Series,
    source: str = 'unknown'
) -> SolderComposition:
    """
    Convenience wrapper to create a SolderComposition from a DataFrame row.

    Args:
        row: A pandas Series representing a single alloy record.
        source: The source identifier for this record.

    Returns:
        A validated SolderComposition instance.

    Raises:
        DataValidationError: If required fields are missing or invalid.
        CompositionSumError: If elemental percentages do not sum to ~100%.
    """
    return SolderComposition.from_dataframe_row(row, source)

def create_descriptor_from_composition(
    composition: SolderComposition,
    clr_values: Tuple[float, ...],
    element_order: List[str],
    mean_atomic_mass: float,
    var_en: float,
    var_radius: float,
    mean_melting_point: float,
    vec: float
) -> CompositionalDescriptor:
    """
    Convenience wrapper to create a CompositionalDescriptor.

    Args:
        composition: The source SolderComposition.
        clr_values: The CLR-transformed composition vector.
        element_order: The ordered list of elements corresponding to clr_values.
        mean_atomic_mass: Weighted mean atomic mass.
        var_en: Electronegativity variance.
        var_radius: Atomic radius variance.
        mean_melting_point: Weighted average melting point.
        vec: Valence electron concentration.

    Returns:
        A CompositionalDescriptor instance.
    """
    return CompositionalDescriptor.from_composition(
        composition,
        clr_values,
        element_order,
        mean_atomic_mass,
        var_en,
        var_radius,
        mean_melting_point,
        vec
    )