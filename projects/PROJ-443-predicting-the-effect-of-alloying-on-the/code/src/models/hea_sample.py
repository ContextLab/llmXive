"""
HEA Sample Entity Structure.

Defines the data model for High-Entropy Alloy (HEA) samples used throughout
the pipeline. This module provides the core dataclass for representing a
 single alloy composition, its calculated features, and target properties.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
import json

# Import validators from the established utility path
from utils.validators import ValidationError, validate_composition_sum


@dataclass
class HEASample:
    """
    Represents a single High-Entropy Alloy sample.

    Attributes:
        sample_id: Unique identifier for the sample (e.g., from OQMD or MP).
        composition: Dictionary mapping element symbols to their atomic fractions.
                     Must sum to 1.0.
        bulk_modulus_observed: Observed bulk modulus in GPa (if available).
        bulk_modulus_miedema: Calculated bulk modulus using Miedema's model (if available).
        bulk_modulus_residual: The residual target (Observed - Miedema).
        features: Dictionary of calculated feature descriptors (e.g., VEC, entropy).
        source: Source of the data (e.g., 'OQMD', 'MaterialsProject', 'Literature').
        alloy_system: Tuple of sorted element symbols representing the system (e.g., ('Al', 'Co', 'Cr', 'Fe', 'Ni')).
        principal_elements: List of elements with atomic fraction >= threshold (default 0.05).
        metadata: Additional arbitrary metadata.
    """
    sample_id: str
    composition: Dict[str, float]
    source: str = "unknown"
    bulk_modulus_observed: Optional[float] = None
    bulk_modulus_miedema: Optional[float] = None
    bulk_modulus_residual: Optional[float] = None
    features: Dict[str, float] = field(default_factory=dict)
    alloy_system: Tuple[str, ...] = field(default_factory=tuple)
    principal_elements: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """
        Initialize derived fields and validate the composition.
        """
        if not self.composition:
            raise ValidationError("Composition cannot be empty.")

        # Validate composition sum
        total = sum(self.composition.values())
        if not validate_composition_sum(total, tolerance=1e-4):
            raise ValidationError(
                f"Composition sum {total:.6f} is not approximately 1.0. "
                f"Sample ID: {self.sample_id}"
            )

        # Derive alloy system (sorted tuple of elements)
        self.alloy_system = tuple(sorted(self.composition.keys()))

        # Identify principal elements (threshold typically 5% or 0.05)
        # Based on task T016 context: "≥5 principal elements"
        principal_threshold = 0.05
        self.principal_elements = [
            elem for elem, frac in self.composition.items()
            if frac >= principal_threshold
        ]

        # If bulk modulus values exist, calculate residual
        if (self.bulk_modulus_observed is not None and
            self.bulk_modulus_miedema is not None):
            self.bulk_modulus_residual = (
                self.bulk_modulus_observed - self.bulk_modulus_miedema
            )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the sample to a dictionary representation.
        """
        return {
            "sample_id": self.sample_id,
            "composition": self.composition,
            "source": self.source,
            "bulk_modulus_observed": self.bulk_modulus_observed,
            "bulk_modulus_miedema": self.bulk_modulus_miedema,
            "bulk_modulus_residual": self.bulk_modulus_residual,
            "features": self.features,
            "alloy_system": list(self.alloy_system),
            "principal_elements": self.principal_elements,
            "metadata": self.metadata
        }

    def to_json(self, indent: Optional[int] = None) -> str:
        """
        Serialize the sample to a JSON string.
        """
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HEASample":
        """
        Create an HEASample instance from a dictionary.
        """
        # Handle alloy_system if it comes in as a list from JSON
        alloy_system = data.get("alloy_system")
        if alloy_system and isinstance(alloy_system, list):
            data["alloy_system"] = tuple(alloy_system)

        return cls(
            sample_id=data["sample_id"],
            composition=data["composition"],
            source=data.get("source", "unknown"),
            bulk_modulus_observed=data.get("bulk_modulus_observed"),
            bulk_modulus_miedema=data.get("bulk_modulus_miedema"),
            bulk_modulus_residual=data.get("bulk_modulus_residual"),
            features=data.get("features", {}),
            alloy_system=data.get("alloy_system", tuple()),
            principal_elements=data.get("principal_elements", []),
            metadata=data.get("metadata", {})
        )


def create_sample_from_row(row: Dict[str, Any], source: str = "unknown") -> HEASample:
    """
    Factory function to create an HEASample from a flat dictionary row
    typically fetched from a CSV or API response.

    Expected row structure:
    - 'sample_id': str
    - 'composition': Dict[str, float] OR a string representation to be parsed
    - 'bulk_modulus': float (optional, mapped to observed)
    - Other fields mapped to features or metadata.

    Args:
        row: Dictionary representing a single data row.
        source: Source identifier.

    Returns:
        HEASample instance.
    """
    sample_id = row.get("sample_id") or row.get("id")
    if not sample_id:
        raise ValidationError("Row missing 'sample_id' or 'id'.")

    # Handle composition: could be a dict or a string like "Al:0.2,Co:0.2..."
    comp_raw = row.get("composition")
    composition = {}
    if isinstance(comp_raw, dict):
        composition = {str(k): float(v) for k, v in comp_raw.items()}
    elif isinstance(comp_raw, str):
        # Simple parser for "El:frac,El:frac" format
        parts = comp_raw.split(",")
        for part in parts:
            if ":" in part:
                elem, val = part.split(":", 1)
                composition[elem.strip()] = float(val.strip())
    else:
        # Fallback: look for columns like 'Al', 'Co' etc. if composition is not explicit
        # This is a heuristic; in strict pipeline, composition should be explicit.
        pass

    if not composition:
        raise ValidationError(f"Could not parse composition for sample {sample_id}.")

    bulk_obs = row.get("bulk_modulus") or row.get("bulk_modulus_observed")
    bulk_mied = row.get("bulk_modulus_miedema")

    # Collect remaining numeric fields as features
    features = {}
    for key, val in row.items():
        if key not in ["sample_id", "id", "composition", "bulk_modulus", "bulk_modulus_observed", "bulk_modulus_miedema"]:
            if isinstance(val, (int, float)) and val is not None:
                features[key] = float(val)

    return HEASample(
        sample_id=sample_id,
        composition=composition,
        source=source,
        bulk_modulus_observed=float(bulk_obs) if bulk_obs is not None else None,
        bulk_modulus_miedema=float(bulk_mied) if bulk_mied is not None else None,
        features=features,
        metadata={"raw_row_keys": list(row.keys())}
    )