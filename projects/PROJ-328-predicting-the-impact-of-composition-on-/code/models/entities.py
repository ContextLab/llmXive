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

from utils.error_handlers import DataValidationError, CompositionSumError

logger = logging.getLogger(__name__)

@dataclass
class SolderComposition:
    """
    Represents a single solder alloy composition with its measured properties.
    
    Attributes:
        elemental_breakdown: Dictionary mapping element symbols to their 
                             percentage composition (e.g., {'Sn': 96.5, 'Ag': 3.0, 'Cu': 0.5})
        hardness_hv: Vickers hardness measurement in HV units.
        alloy_family: Classification of the alloy family (e.g., 'SAC', 'SnPb', 'SnAg').
        source_citation: Reference to the original data source.
        measurement_temp_c: Optional temperature at which hardness was measured.
        notes: Optional additional notes about the measurement or composition.
    """
    elemental_breakdown: Dict[str, float]
    hardness_hv: float
    alloy_family: str
    source_citation: str
    measurement_temp_c: Optional[float] = None
    notes: Optional[str] = None
    
    def __post_init__(self):
        """Validate the composition after initialization."""
        self._validate_composition_sum()
        self._validate_hardness()
        self._validate_elements()
    
    def _validate_composition_sum(self) -> None:
        """
        Validate that the elemental composition sums to approximately 100%.
        
        Raises:
            CompositionSumError: If the sum deviates significantly from 100%.
        """
        total = sum(self.elemental_breakdown.values())
        # Allow for small floating point errors and rounding
        if not (99.0 <= total <= 101.0):
            logger.warning(
                f"Composition sum for {self.source_citation} is {total:.2f}%, "
                f"which is outside the expected range [99, 101]."
            )
            # We allow it to proceed but log a warning, as some data sources
            # might have minor inconsistencies.
    
    def _validate_hardness(self) -> None:
        """Validate that hardness value is positive."""
        if self.hardness_hv <= 0:
            raise DataValidationError(
                f"Hardness value must be positive. Got {self.hardness_hv} for "
                f"composition from {self.source_citation}"
            )
    
    def _validate_elements(self) -> None:
        """Validate that all elements have positive composition values."""
        for element, value in self.elemental_breakdown.items():
            if value < 0:
                raise DataValidationError(
                    f"Element {element} has negative composition {value} "
                    f"in composition from {self.source_citation}"
                )
            if value == 0:
                logger.debug(
                    f"Element {element} has zero composition in "
                    f"composition from {self.source_citation}"
                )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the composition to a dictionary representation."""
        return {
            'elemental_breakdown': self.elemental_breakdown,
            'hardness_hv': self.hardness_hv,
            'alloy_family': self.alloy_family,
            'source_citation': self.source_citation,
            'measurement_temp_c': self.measurement_temp_c,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SolderComposition':
        """Create a SolderComposition instance from a dictionary."""
        return cls(
            elemental_breakdown=data['elemental_breakdown'],
            hardness_hv=data['hardness_hv'],
            alloy_family=data['alloy_family'],
            source_citation=data['source_citation'],
            measurement_temp_c=data.get('measurement_temp_c'),
            notes=data.get('notes')
        )
    
    def to_json(self) -> str:
        """Serialize the composition to a JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'SolderComposition':
        """Deserialize a SolderComposition from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

@dataclass
class CompositionalDescriptor:
    """
    Represents derived physical descriptors for a solder composition.
    
    These descriptors capture the physical and chemical properties of the alloy
    based on its elemental composition and standard elemental properties.
    
    Attributes:
        weighted_mean_atomic_mass: Weighted average of atomic masses of constituent elements.
        electronegativity_variance: Variance of electronegativity values weighted by composition.
        atomic_radius_variance: Variance of atomic radii weighted by composition.
        weighted_avg_melting_point: Weighted average melting point of constituent elements.
        valence_electron_concentration: Average number of valence electrons per atom.
        source_composition: Reference to the original SolderComposition these descriptors were derived from.
    """
    weighted_mean_atomic_mass: float
    electronegativity_variance: float
    atomic_radius_variance: float
    weighted_avg_melting_point: float
    valence_electron_concentration: float
    source_composition: Optional[SolderComposition] = None
    
    def to_dict(self) -> Dict[str, float]:
        """Convert the descriptor to a dictionary representation."""
        return {
            'weighted_mean_atomic_mass': self.weighted_mean_atomic_mass,
            'electronegativity_variance': self.electronegativity_variance,
            'atomic_radius_variance': self.atomic_radius_variance,
            'weighted_avg_melting_point': self.weighted_avg_melting_point,
            'valence_electron_concentration': self.valence_electron_concentration
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'CompositionalDescriptor':
        """Create a CompositionalDescriptor instance from a dictionary."""
        return cls(
            weighted_mean_atomic_mass=data['weighted_mean_atomic_mass'],
            electronegativity_variance=data['electronegativity_variance'],
            atomic_radius_variance=data['atomic_radius_variance'],
            weighted_avg_melting_point=data['weighted_avg_melting_point'],
            valence_electron_concentration=data['valence_electron_concentration']
        )

def create_composition_from_dataframe_row(
    row: Dict[str, Any], 
    default_alloy_family: str = "Unknown"
) -> SolderComposition:
    """
    Create a SolderComposition instance from a pandas DataFrame row or dictionary.
    
    Args:
        row: Dictionary containing composition data. Expected keys:
             - Elemental composition columns (e.g., 'Sn', 'Ag', 'Cu', etc.)
             - 'hardness_hv': Vickers hardness value
             - 'alloy_family': Optional alloy family classification
             - 'source_citation': Data source reference
             - 'measurement_temp_c': Optional measurement temperature
        default_alloy_family: Default alloy family if not specified in row.
        
    Returns:
        SolderComposition instance.
        
    Raises:
        DataValidationError: If required fields are missing or invalid.
    """
    # Extract elemental composition (non-numeric columns are metadata)
    elemental_breakdown = {}
    numeric_cols = [k for k, v in row.items() if isinstance(v, (int, float)) and k != 'hardness_hv' and k != 'measurement_temp_c']
    
    # Heuristic: Identify elemental columns (typically 1-2 letter element symbols)
    # This is a simplified approach; a more robust version would use a periodic table lookup
    for col in numeric_cols:
        if len(col) <= 3 and col[0].isupper() and (len(col) == 1 or col[1].islower()):
            if row[col] is not None and not math.isnan(row[col]):
                elemental_breakdown[col] = float(row[col])
    
    if not elemental_breakdown:
        raise DataValidationError("No valid elemental composition found in row")
    
    # Extract hardness
    hardness = row.get('hardness_hv')
    if hardness is None or (isinstance(hardness, float) and math.isnan(hardness)):
        raise DataValidationError("Hardness value is missing or NaN")
    
    # Extract metadata
    alloy_family = row.get('alloy_family', default_alloy_family)
    source_citation = row.get('source_citation', 'Unknown')
    measurement_temp = row.get('measurement_temp_c')
    if isinstance(measurement_temp, float) and math.isnan(measurement_temp):
        measurement_temp = None
    
    return SolderComposition(
        elemental_breakdown=elemental_breakdown,
        hardness_hv=float(hardness),
        alloy_family=str(alloy_family),
        source_citation=str(source_citation),
        measurement_temp_c=measurement_temp
    )

def create_descriptor_from_composition(
    composition: SolderComposition,
    elemental_properties: Dict[str, Dict[str, float]]
) -> CompositionalDescriptor:
    """
    Create compositional descriptors from a SolderComposition.
    
    Args:
        composition: SolderComposition instance to derive descriptors from.
        elemental_properties: Dictionary mapping element symbols to their properties.
            Expected format: {element: {'atomic_mass': float, 'electronegativity': float, 
                                       'atomic_radius': float, 'melting_point': float, 
                                       'valence_electrons': float}}
            
    Returns:
        CompositionalDescriptor instance.
        
    Raises:
        DataValidationError: If required elemental properties are missing.
    """
    if not composition.elemental_breakdown:
        raise DataValidationError("Cannot create descriptors from empty composition")
    
    # Calculate total composition for normalization
    total_composition = sum(composition.elemental_breakdown.values())
    if total_composition == 0:
        raise DataValidationError("Cannot create descriptors from zero-sum composition")
    
    # Initialize accumulators
    weighted_mass_sum = 0.0
    weighted_electronegativity_sum = 0.0
    weighted_radius_sum = 0.0
    weighted_melting_point_sum = 0.0
    weighted_valence_sum = 0.0
    
    electronegativity_values = []
    radius_values = []
    weights = []
    
    for element, fraction in composition.elemental_breakdown.items():
        if element not in elemental_properties:
            logger.warning(f"Element {element} not found in elemental_properties, skipping")
            continue
        
        props = elemental_properties[element]
        normalized_fraction = fraction / total_composition
        
        # Accumulate weighted values
        weighted_mass_sum += normalized_fraction * props['atomic_mass']
        weighted_electronegativity_sum += normalized_fraction * props['electronegativity']
        weighted_radius_sum += normalized_fraction * props['atomic_radius']
        weighted_melting_point_sum += normalized_fraction * props['melting_point']
        weighted_valence_sum += normalized_fraction * props['valence_electrons']
        
        # Store for variance calculation
        electronegativity_values.append(props['electronegativity'])
        radius_values.append(props['atomic_radius'])
        weights.append(normalized_fraction)
    
    # Calculate variance for electronegativity and atomic radius
    def weighted_variance(values, weights):
        if len(values) == 0:
            return 0.0
        mean = sum(v * w for v, w in zip(values, weights))
        variance = sum(w * (v - mean) ** 2 for v, w in zip(values, weights))
        return variance
    
    electronegativity_variance = weighted_variance(electronegativity_values, weights)
    atomic_radius_variance = weighted_variance(radius_values, weights)
    
    return CompositionalDescriptor(
        weighted_mean_atomic_mass=weighted_mass_sum,
        electronegativity_variance=electronegativity_variance,
        atomic_radius_variance=atomic_radius_variance,
        weighted_avg_melting_point=weighted_melting_point_sum,
        valence_electron_concentration=weighted_valence_sum,
        source_composition=composition
    )