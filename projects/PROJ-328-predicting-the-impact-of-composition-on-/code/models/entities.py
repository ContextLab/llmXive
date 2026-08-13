"""
Data models and entities for solder alloy analysis.

This module defines the core data structures for representing solder
compositions and their derived compositional descriptors.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
import json
import math
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)

@dataclass
class SolderComposition:
    """
    Represents a single solder alloy composition.

    Attributes:
        alloy_id: Unique identifier for the alloy (e.g., from source database)
        elements: Dictionary mapping element symbol to weight percentage (0-100)
        hardness_hv: Vickers hardness value (HV)
        measurement_temp_c: Temperature at which hardness was measured (Celsius)
        source: Original data source identifier (e.g., 'Materials Project', 'NIST')
        reference: Citation or DOI for the data point
        notes: Optional notes or flags (e.g., 'manual_review')
    """
    alloy_id: str
    elements: Dict[str, float]
    hardness_hv: Optional[float] = None
    measurement_temp_c: Optional[float] = None
    source: str = "unknown"
    reference: Optional[str] = None
    notes: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate composition data after initialization."""
        # Validate elements are non-negative
        for elem, pct in self.elements.items():
            if pct < 0:
                raise ValueError(f"Element {elem} has negative percentage: {pct}")
        
        # Validate hardness if present
        if self.hardness_hv is not None and self.hardness_hv <= 0:
            raise ValueError(f"Hardness must be positive: {self.hardness_hv}")

    def composition_sum(self) -> float:
        """Calculate the sum of all elemental percentages."""
        return sum(self.elements.values())

    def is_valid_composition(self, threshold: float = 0.95) -> bool:
        """
        Check if the composition sums to approximately 100% (or 1.0).

        Args:
            threshold: Minimum acceptable sum (e.g., 0.95 for 95%)

        Returns:
            True if sum is within threshold, False otherwise
        """
        total = self.composition_sum()
        # Normalize to 0-1 scale if input is 0-100
        if total > 1.0:
            total = total / 100.0
        return total >= threshold

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'alloy_id': self.alloy_id,
            'elements': self.elements,
            'hardness_hv': self.hardness_hv,
            'measurement_temp_c': self.measurement_temp_c,
            'source': self.source,
            'reference': self.reference,
            'notes': self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SolderComposition':
        """Create instance from dictionary."""
        return cls(
            alloy_id=data['alloy_id'],
            elements=data.get('elements', {}),
            hardness_hv=data.get('hardness_hv'),
            measurement_temp_c=data.get('measurement_temp_c'),
            source=data.get('source', 'unknown'),
            reference=data.get('reference'),
            notes=data.get('notes', [])
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'SolderComposition':
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

@dataclass
class CompositionalDescriptor:
    """
    Represents computed descriptors derived from a solder composition.

    These descriptors are used as features in machine learning models.
    They capture physical and chemical properties of the alloy.

    Attributes:
        alloy_id: Reference to the source SolderComposition
        descriptors: Dictionary of computed descriptor values
        raw_composition: The original composition used for calculation
    """
    alloy_id: str
    descriptors: Dict[str, float] = field(default_factory=dict)
    raw_composition: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure descriptors are valid numbers."""
        for name, value in self.descriptors.items():
            if not isinstance(value, (int, float)) or math.isnan(value) or math.isinf(value):
                logger.warning(f"Invalid descriptor value for {name}: {value}")

    def add_descriptor(self, name: str, value: float):
        """Add or update a descriptor value."""
        if math.isnan(value) or math.isinf(value):
            logger.warning(f"Skipping invalid descriptor {name} = {value}")
            return
        self.descriptors[name] = value

    def get_descriptor(self, name: str, default: float = 0.0) -> float:
        """Get a descriptor value or return default if not present."""
        return self.descriptors.get(name, default)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'alloy_id': self.alloy_id,
            'descriptors': self.descriptors,
            'raw_composition': self.raw_composition
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CompositionalDescriptor':
        """Create instance from dictionary."""
        return cls(
            alloy_id=data['alloy_id'],
            descriptors=data.get('descriptors', {}),
            raw_composition=data.get('raw_composition', {})
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'CompositionalDescriptor':
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

def create_composition_from_dataframe_row(row: Any, config: Optional[Dict[str, Any]] = None) -> SolderComposition:
    """
    Create a SolderComposition instance from a pandas DataFrame row.

    Args:
        row: A pandas Series or dictionary-like row
        config: Optional configuration dict for column mapping

    Returns:
        SolderComposition instance

    Raises:
        ValueError: If required fields are missing or invalid
    """
    # Default column mappings
    col_map = config or {
        'id': 'alloy_id',
        'elements': ['Sn', 'Ag', 'Cu', 'Bi', 'In', 'Pb', 'Sb', 'Zn', 'Ni', 'Co'],
        'hardness': 'hardness_hv',
        'temp': 'measurement_temp_c',
        'source': 'source'
    }

    # Extract ID
    alloy_id = row.get(col_map['id']) or row.get('alloy_id')
    if not alloy_id:
        raise ValueError("Missing alloy_id in row")

    # Extract elements
    elements = {}
    for elem in col_map['elements']:
        if elem in row:
            val = row[elem]
            if pd.notna(val) and val > 0:
                elements[elem] = float(val)
    
    # If no elements found, try to find any column that looks like an element
    if not elements:
        element_cols = [k for k in row.keys() if k in ['Sn', 'Ag', 'Cu', 'Bi', 'In', 'Pb', 'Sb', 'Zn', 'Ni', 'Co']]
        for col in element_cols:
            val = row[col]
            if pd.notna(val) and val > 0:
                elements[col] = float(val)

    if not elements:
        raise ValueError(f"No valid elemental composition found for alloy {alloy_id}")

    # Extract hardness
    hardness = row.get(col_map['hardness']) or row.get('hardness_hv')
    if pd.notna(hardness):
        hardness = float(hardness)

    # Extract temperature
    temp = row.get(col_map['temp']) or row.get('measurement_temp_c')
    if pd.notna(temp):
        temp = float(temp)

    # Extract source
    source = row.get(col_map['source']) or row.get('source', 'unknown')

    return SolderComposition(
        alloy_id=str(alloy_id),
        elements=elements,
        hardness_hv=hardness,
        measurement_temp_c=temp,
        source=source
    )

def create_descriptor_from_composition(
    composition: SolderComposition, 
    descriptors: Optional[Dict[str, float]] = None
) -> CompositionalDescriptor:
    """
    Create a CompositionalDescriptor from a SolderComposition.

    Args:
        composition: Source SolderComposition instance
        descriptors: Optional pre-computed descriptors

    Returns:
        CompositionalDescriptor instance
    """
    desc = CompositionalDescriptor(
        alloy_id=composition.alloy_id,
        raw_composition=composition.elements
    )

    if descriptors:
        for name, value in descriptors.items():
            desc.add_descriptor(name, value)

    return desc