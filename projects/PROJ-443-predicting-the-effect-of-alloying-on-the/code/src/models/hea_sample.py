"""
HEA Sample Entity Module.

Defines the HEASample dataclass and helper functions for creating samples
from raw data rows. This module serves as the core data structure for
High-Entropy Alloy research data, ensuring type safety and validation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
import json

from utils.validators import ValidationError, validate_composition_sum


@dataclass
class HEASample:
    """
    Represents a single High-Entropy Alloy (HEA) sample with its composition
    and associated properties.

    Attributes:
        sample_id: Unique identifier for the sample.
        composition: Dictionary mapping element symbols to their atomic fractions.
        bulk_modulus: Observed bulk modulus in GPa.
        source: Data source identifier (e.g., 'OQMD', 'MaterialsProject').
        temperature: Measurement temperature in Kelvin (optional).
        pressure: Measurement pressure in GPa (optional).
        metadata: Additional key-value pairs for provenance or experimental details.
    """
    sample_id: str
    composition: Dict[str, float]
    bulk_modulus: Optional[float] = None
    source: Optional[str] = None
    temperature: Optional[float] = None
    pressure: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate composition sum and types after initialization."""
        if not self.composition:
            raise ValidationError("Composition cannot be empty.")

        # Validate composition sum
        total_sum = sum(self.composition.values())
        if not validate_composition_sum(total_sum):
            raise ValidationError(
                f"Composition sum must be approximately 1.0. "
                f"Got: {total_sum:.6f}"
            )

        # Validate element symbols are strings
        for element, fraction in self.composition.items():
            if not isinstance(element, str):
                raise ValidationError(f"Element key must be a string, got {type(element)}")
            if not isinstance(fraction, (int, float, Decimal)):
                raise ValidationError(
                    f"Composition fraction for {element} must be numeric, got {type(fraction)}"
                )
            if fraction < 0:
                raise ValidationError(
                    f"Composition fraction for {element} cannot be negative: {fraction}"
                )

    @property
    def elements(self) -> List[str]:
        """Return sorted list of elements in the composition."""
        return sorted(self.composition.keys())

    @property
    def num_elements(self) -> int:
        """Return the number of principal elements in the alloy."""
        return len(self.composition)

    @property
    def is_high_entropy(self) -> bool:
        """
        Determine if the sample qualifies as a High-Entropy Alloy.
        Convention: >= 5 principal elements with atomic fractions >= 0.05.
        """
        return (
            self.num_elements >= 5 and
            all(frac >= 0.05 for frac in self.composition.values())
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the sample to a dictionary representation."""
        return {
            "sample_id": self.sample_id,
            "composition": self.composition,
            "bulk_modulus": self.bulk_modulus,
            "source": self.source,
            "temperature": self.temperature,
            "pressure": self.pressure,
            "metadata": self.metadata,
            "num_elements": self.num_elements,
            "is_high_entropy": self.is_high_entropy,
        }

    def to_json(self, indent: Optional[int] = 2) -> str:
        """Serialize the sample to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HEASample":
        """Create an HEASample instance from a dictionary."""
        composition = data.get("composition", {})
        if not isinstance(composition, dict):
            raise ValidationError("Invalid composition format in source data")

        return cls(
            sample_id=str(data.get("sample_id", "")),
            composition=composition,
            bulk_modulus=data.get("bulk_modulus"),
            source=data.get("source"),
            temperature=data.get("temperature"),
            pressure=data.get("pressure"),
            metadata=data.get("metadata", {}),
        )


def create_sample_from_row(
    row: Dict[str, Any],
    composition_prefix: str = "element_",
    bulk_modulus_col: str = "bulk_modulus",
    source_col: str = "source",
    sample_id_col: str = "id"
) -> HEASample:
    """
    Create an HEASample instance from a flat dictionary row (e.g., from a CSV/DB).

    This function extracts composition data based on a prefix convention
    (e.g., 'element_Fe', 'element_Cr') and maps other columns to the sample attributes.

    Args:
        row: Flat dictionary containing sample data.
        composition_prefix: Prefix for composition columns (e.g., 'element_').
        bulk_modulus_col: Column name for bulk modulus.
        source_col: Column name for data source.
        sample_id_col: Column name for sample ID.

    Returns:
        HEASample instance.

    Raises:
        ValidationError: If required fields are missing or invalid.
    """
    # Extract composition
    composition = {}
    for key, value in row.items():
        if key.startswith(composition_prefix):
            element = key.replace(composition_prefix, "")
            if value is not None and float(value) > 0:
                composition[element] = float(value)

    if not composition:
        raise ValidationError("No valid composition data found in row")

    # Validate composition sum before creating object
    total_sum = sum(composition.values())
    if not validate_composition_sum(total_sum):
        # Attempt normalization if close to 1.0 to handle floating point drift
        if 0.99 < total_sum < 1.01:
            composition = {k: v / total_sum for k, v in composition.items()}
        else:
            raise ValidationError(
                f"Row composition sum {total_sum:.6f} deviates significantly from 1.0"
            )

    # Extract other fields
    sample_id = row.get(sample_id_col)
    if not sample_id:
        # Generate a temporary ID if missing
        sample_id = f"auto_{hash(frozenset(composition.items()))}"

    bulk_modulus_val = row.get(bulk_modulus_col)
    if bulk_modulus_val is not None:
        try:
            bulk_modulus_val = float(bulk_modulus_val)
        except (ValueError, TypeError):
            bulk_modulus_val = None

    return HEASample(
        sample_id=str(sample_id),
        composition=composition,
        bulk_modulus=bulk_modulus_val,
        source=row.get(source_col),
        temperature=row.get("temperature"),
        pressure=row.get("pressure"),
        metadata={k: v for k, v in row.items() if not k.startswith(composition_prefix) and k not in [bulk_modulus_col, source_col, sample_id_col, "temperature", "pressure"]}
    )