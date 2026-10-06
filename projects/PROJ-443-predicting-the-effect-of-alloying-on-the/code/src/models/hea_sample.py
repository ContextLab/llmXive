"""
HEASample: Data structure representing a single High-Entropy Alloy (HEA) sample.

This module defines the core entity structure for HEA data, including composition,
calculated features, and target variables. It enforces data integrity constraints
such as composition sum validation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
import json

# Import from existing project utilities
from utils.validators import ValidationError, validate_composition_sum


@dataclass
class HEASample:
    """
    Represents a single High-Entropy Alloy sample.
    
    Attributes:
        sample_id: Unique identifier for the sample (e.g., from OQMD or Materials Project)
        composition: Dictionary mapping element symbols to their atomic fractions
        bulk_modulus_observed: Observed bulk modulus in GPa
        bulk_modulus_miedema: Calculated Miedema bulk modulus in GPa (optional)
        bulk_modulus_residual: Residual (Observed - Miedema) in GPa (optional)
        descriptors: Dictionary of calculated feature descriptors
        ilr_composition: Isometric Log-Ratio transformed composition (optional)
        source: Data source identifier ('oqmd', 'mp', 'literature')
        metadata: Additional arbitrary metadata
    """
    sample_id: str
    composition: Dict[str, float]
    bulk_modulus_observed: Optional[float] = None
    bulk_modulus_miedema: Optional[float] = None
    bulk_modulus_residual: Optional[float] = None
    descriptors: Dict[str, float] = field(default_factory=dict)
    ilr_composition: Optional[Tuple[float, ...]] = None
    source: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate composition sum after initialization."""
        if self.composition:
            try:
                validate_composition_sum(self.composition)
            except ValidationError as e:
                raise ValidationError(
                    f"Invalid composition for sample {self.sample_id}: {e}"
                )
    
    @property
    def elements(self) -> List[str]:
        """Return sorted list of elements in the composition."""
        return sorted(self.composition.keys())
    
    @property
    def num_elements(self) -> int:
        """Return the number of principal elements."""
        return len(self.composition)
    
    @property
    def is_hea(self) -> bool:
        """Check if this sample qualifies as a High-Entropy Alloy (>= 5 elements)."""
        return self.num_elements >= 5
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the sample to a dictionary representation."""
        return {
            "sample_id": self.sample_id,
            "composition": self.composition,
            "bulk_modulus_observed": self.bulk_modulus_observed,
            "bulk_modulus_miedema": self.bulk_modulus_miedema,
            "bulk_modulus_residual": self.bulk_modulus_residual,
            "descriptors": self.descriptors,
            "ilr_composition": list(self.ilr_composition) if self.ilr_composition else None,
            "source": self.source,
            "metadata": self.metadata,
            "num_elements": self.num_elements,
            "is_hea": self.is_hea
        }
    
    def to_json(self, indent: Optional[int] = None) -> str:
        """Serialize the sample to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HEASample":
        """Create a HEASample from a dictionary."""
        # Handle ILR composition conversion if present
        ilr_comp = data.get("ilr_composition")
        if ilr_comp is not None:
            ilr_comp = tuple(ilr_comp)
        
        return cls(
            sample_id=data["sample_id"],
            composition=data["composition"],
            bulk_modulus_observed=data.get("bulk_modulus_observed"),
            bulk_modulus_miedema=data.get("bulk_modulus_miedema"),
            bulk_modulus_residual=data.get("bulk_modulus_residual"),
            descriptors=data.get("descriptors", {}),
            ilr_composition=ilr_comp,
            source=data.get("source", "unknown"),
            metadata=data.get("metadata", {})
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> "HEASample":
        """Create a HEASample from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def validate(self) -> bool:
        """
        Perform comprehensive validation of the sample.
        
        Returns:
            True if valid, raises ValidationError otherwise.
        """
        # Validate composition sum
        validate_composition_sum(self.composition)
        
        # Validate bulk modulus if present
        if self.bulk_modulus_observed is not None:
            if self.bulk_modulus_observed <= 0:
                raise ValidationError(
                    f"Bulk modulus must be positive for sample {self.sample_id}"
                )
        
        # Validate Miedema calculation if present
        if self.bulk_modulus_miedema is not None:
            if self.bulk_modulus_miedema <= 0:
                raise ValidationError(
                    f"Miedema bulk modulus must be positive for sample {self.sample_id}"
                )
        
        # Validate residual if present
        if self.bulk_modulus_residual is not None:
            # Residual can be negative, but should be finite
            if not (self.bulk_modulus_residual == self.bulk_modulus_residual):  # NaN check
                raise ValidationError(
                    f"Residual bulk modulus is NaN for sample {self.sample_id}"
                )
        
        return True
    
    def __repr__(self) -> str:
        return (
            f"HEASample(id={self.sample_id}, "
            f"elements={self.num_elements}, "
            f"source={self.source})"
        )

def create_sample_from_row(
    row: Dict[str, Any],
    composition_columns: List[str],
    source: str = "unknown"
) -> HEASample:
    """
    Create a HEASample from a dictionary row (e.g., from a pandas DataFrame).
    
    Args:
        row: Dictionary representing a single row of data
        composition_columns: List of column names that represent composition fractions
        source: Data source identifier
        
    Returns:
        HEASample instance
        
    Raises:
        ValidationError: If composition validation fails
        KeyError: If required fields are missing
    """
    # Extract composition
    composition = {}
    for col in composition_columns:
        if col in row and row[col] is not None and row[col] > 0:
            # Convert to float to ensure numeric type
            composition[col] = float(row[col])
    
    if not composition:
        raise ValidationError("No valid composition data found in row")
    
    # Extract bulk modulus
    bulk_mod_obs = None
    if "bulk_modulus_observed" in row:
        val = row["bulk_modulus_observed"]
        if val is not None:
            bulk_mod_obs = float(val)
    
    bulk_mod_miedema = None
    if "bulk_modulus_miedema" in row:
        val = row["bulk_modulus_miedema"]
        if val is not None:
            bulk_mod_miedema = float(val)
    
    bulk_mod_residual = None
    if "bulk_modulus_residual" in row:
        val = row["bulk_modulus_residual"]
        if val is not None:
            bulk_mod_residual = float(val)
    
    # Extract descriptors (all other numeric columns that aren't metadata)
    descriptors = {}
    exclude_cols = set(composition_columns) | {
        "sample_id", "bulk_modulus_observed", "bulk_modulus_miedema", 
        "bulk_modulus_residual", "source", "metadata"
    }
    
    for key, value in row.items():
        if key not in exclude_cols and value is not None:
            try:
                descriptors[key] = float(value)
            except (ValueError, TypeError):
                # Skip non-numeric values
                pass
    
    # Create sample
    sample_id = row.get("sample_id", "unknown")
    
    sample = HEASample(
        sample_id=str(sample_id),
        composition=composition,
        bulk_modulus_observed=bulk_mod_obs,
        bulk_modulus_miedema=bulk_mod_miedema,
        bulk_modulus_residual=bulk_mod_residual,
        descriptors=descriptors,
        source=source,
        metadata={}
    )
    
    return sample