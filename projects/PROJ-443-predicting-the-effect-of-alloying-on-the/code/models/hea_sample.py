"""
HEA Sample Entity Structure.

Defines the data model for High-Entropy Alloy (HEA) samples used throughout
the pipeline. This module provides the core dataclasses and validation logic
for representing alloy compositions, properties, and metadata.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
import json

from utils.validators import ValidationError, validate_composition_sum


@dataclass
class HEASample:
    """
    Represents a single High-Entropy Alloy sample.

    Attributes:
        sample_id: Unique identifier for the sample (e.g., OQMD or MP ID).
        source: Data source identifier ('OQMD', 'MP', 'Literature').
        composition: Dictionary mapping element symbols to atomic fractions.
                     Sum of values must be 1.0 (validated).
        bulk_modulus: Observed Bulk Modulus in GPa.
        bulk_modulus_miedema: Calculated Bulk Modulus via Miedema's model (GPa).
        bulk_modulus_residual: Residual (Observed - Miedema) in GPa.
        elements: List of element symbols present in the alloy.
        num_elements: Number of principal elements (derived from composition).
        is_hea: Boolean flag; True if num_elements >= 5.
        metadata: Dictionary for additional provenance or experimental details.
    """
    sample_id: str
    source: str
    composition: Dict[str, float]
    bulk_modulus: Optional[float] = None
    bulk_modulus_miedema: Optional[float] = None
    bulk_modulus_residual: Optional[float] = None
    elements: List[str] = field(default_factory=list)
    num_elements: int = 0
    is_hea: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize derived fields and validate composition."""
        if not self.composition:
            raise ValidationError("Composition cannot be empty.")

        # Derive elements and count
        self.elements = sorted(list(self.composition.keys()))
        self.num_elements = len(self.elements)

        # HEA definition: >= 5 principal elements
        self.is_hea = self.num_elements >= 5

        # Validate composition sum
        validate_composition_sum(self.composition, tolerance=1e-6)

        # Calculate residual if both observed and Miedema values exist
        if self.bulk_modulus is not None and self.bulk_modulus_miedema is not None:
            self.bulk_modulus_residual = self.bulk_modulus - self.bulk_modulus_miedema

    def to_dict(self) -> Dict[str, Any]:
        """Convert the sample to a dictionary representation."""
        return {
            "sample_id": self.sample_id,
            "source": self.source,
            "composition": self.composition,
            "bulk_modulus": self.bulk_modulus,
            "bulk_modulus_miedema": self.bulk_modulus_miedema,
            "bulk_modulus_residual": self.bulk_modulus_residual,
            "elements": self.elements,
            "num_elements": self.num_elements,
            "is_hea": self.is_hea,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HEASample":
        """
        Create an HEASample instance from a dictionary.

        Args:
            data: Dictionary containing sample data.

        Returns:
            An instantiated HEASample object.
        """
        # Handle nested metadata if necessary
        metadata = data.get("metadata", {})
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except json.JSONDecodeError:
                metadata = {"raw": metadata}

        return cls(
            sample_id=data["sample_id"],
            source=data["source"],
            composition=data["composition"],
            bulk_modulus=data.get("bulk_modulus"),
            bulk_modulus_miedema=data.get("bulk_modulus_miedema"),
            metadata=metadata
        )

    def __repr__(self) -> str:
        return (
            f"HEASample(id={self.sample_id}, elements={self.elements}, "
            f"is_hea={self.is_hea}, bulk_modulus={self.bulk_modulus})"
        )


# Helper functions for batch processing
def create_sample_from_row(row: Dict[str, Any], source: str = "Unknown") -> HEASample:
    """
    Factory function to create an HEASample from a pandas-like row dictionary.

    Args:
        row: Dictionary representing a single row of data.
        source: Default source if not specified in the row.

    Returns:
        HEASample instance.
    """
    sample_id = row.get("sample_id", row.get("id", "unknown"))
    composition = row.get("composition", {})

    # Ensure composition values are floats
    composition = {k: float(v) for k, v in composition.items()}

    bulk_modulus = row.get("bulk_modulus")
    if bulk_modulus is not None:
        bulk_modulus = float(bulk_modulus)

    bulk_modulus_miedema = row.get("bulk_modulus_miedema")
    if bulk_modulus_miedema is not None:
        bulk_modulus_miedema = float(bulk_modulus_miedema)

    metadata = row.get("metadata", {})
    if not metadata and "source" in row:
        metadata = {"source_override": row["source"]}

    return HEASample(
        sample_id=str(sample_id),
        source=source,
        composition=composition,
        bulk_modulus=bulk_modulus,
        bulk_modulus_miedema=bulk_modulus_miedema,
        metadata=metadata
    )