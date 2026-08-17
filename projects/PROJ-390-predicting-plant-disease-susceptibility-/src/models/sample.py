"""
Data model for biological samples (plants).
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import numpy as np


class Species(Enum):
    """Enumeration of supported plant species."""
    WHEAT = "wheat"
    RICE = "rice"
    MAIZE = "maize"
    TOMATO = "tomato"
    SOYBEAN = "soybean"


@dataclass
class Sample:
    """
    Represents a biological sample with genomic and environmental metadata.

    Attributes:
        sample_id: Unique identifier for the sample.
        species: The plant species (Enum).
        accession_id: Reference genome accession ID (e.g., GCA_000003205.5).
        latitude: Geographic latitude of sample collection.
        longitude: Geographic longitude of sample collection.
        collection_date: Date of sample collection (YYYY-MM-DD).
        disease_status: Binary label (1 for susceptible, 0 for resistant).
        phenotype_source: Source of the disease label (e.g., 'field-trial-db').
        genomic_features: List of genomic feature objects associated with this sample.
        environmental_features: Dict of environmental features (temp, humidity, etc.).
        metadata: Additional arbitrary metadata.
    """
    sample_id: str
    species: Species
    accession_id: str
    latitude: float
    longitude: float
    collection_date: str
    disease_status: int
    phenotype_source: str
    genomic_features: List[Any] = field(default_factory=list)
    environmental_features: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_genomic_feature(self, feature: Any) -> None:
        """Add a genomic feature to the sample."""
        self.genomic_features.append(feature)

    def add_environmental_feature(self, key: str, value: float) -> None:
        """Add an environmental feature to the sample."""
        self.environmental_features[key] = value

    def get_feature_vector(self) -> np.ndarray:
        """
        Construct a numerical feature vector from genomic and environmental features.
        Assumes features have a 'value' attribute or are already numeric.
        """
        values = []
        # Flatten genomic features
        for f in self.genomic_features:
            if hasattr(f, 'value'):
                values.append(f.value)
            else:
                values.append(float(f))

        # Append environmental features (sorted by key for consistency)
        for key in sorted(self.environmental_features.keys()):
            values.append(self.environmental_features[key])

        return np.array(values, dtype=np.float64)

    def is_valid(self) -> bool:
        """Check if the sample has all required fields populated."""
        if not self.sample_id or not self.species or not self.accession_id:
            return False
        if self.latitude is None or self.longitude is None:
            return False
        if self.disease_status not in [0, 1]:
            return False
        if not self.phenotype_source:
            return False
        return True
