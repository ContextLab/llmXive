"""
Data models for features in the plant disease susceptibility study.
"""
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum


class FeatureType(Enum):
    """Type of feature in the dataset."""
    GENOMIC = "genomic"
    ENVIRONMENTAL = "environmental"


@dataclass
class Feature:
    """
    Represents a single feature (predictor variable) in the dataset.

    Attributes:
        name: The name of the feature (e.g., SNP ID or environmental variable name).
        feature_type: Whether this is a genomic or environmental feature.
        source: The original source of the data (e.g., 'NCBI-SRA', 'ERA5-Land').
        description: Optional description of what the feature represents.
        unit: Optional unit of measurement (e.g., 'Celsius', 'mm').
    """
    name: str
    feature_type: FeatureType
    source: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[str] = None

    def to_dict(self) -> Dict[str, str]:
        """Convert the feature to a dictionary representation."""
        return {
            "name": self.name,
            "feature_type": self.feature_type.value,
            "source": self.source,
            "description": self.description,
            "unit": self.unit
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "Feature":
        """Create a Feature instance from a dictionary."""
        type_str = data.get("feature_type", "").lower()
        try:
            ftype = FeatureType(type_str)
        except ValueError:
            raise ValueError(f"Unsupported feature type: {type_str}")

        return cls(
            name=data["name"],
            feature_type=ftype,
            source=data.get("source"),
            description=data.get("description"),
            unit=data.get("unit")
        )
