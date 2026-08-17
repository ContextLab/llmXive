"""
Data models for plant disease susceptibility prediction.
Defines the core entity: Sample.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import numpy as np


class Species(Enum):
    """Supported plant species for the study."""
    WHEAT = "wheat"
    RICE = "rice"
    MAIZE = "maize"
    TOMATO = "tomato"
    SOYBEAN = "soybean"


@dataclass
class Sample:
    """
    Represents a single biological sample with associated genomic and environmental data.

    Attributes:
        sample_id: Unique identifier for the sample (e.g., SRA accession).
        species: The plant species of the sample.
        genomic_features: Dictionary mapping SNP IDs to allele frequencies or genotypes.
        environmental_features: Dictionary mapping environmental variable names to values.
        disease_status: Binary label (1 for susceptible, 0 for resistant/healthy).
        latitude: Geographic latitude of sample collection.
        longitude: Geographic longitude of sample collection.
        collection_date: Date of sample collection (YYYY-MM-DD).
        phenotype_source: Source of the disease susceptibility label (e.g., 'field-trial-db').
        metadata: Additional arbitrary metadata.
    """
    sample_id: str
    species: Species
    genomic_features: Dict[str, float] = field(default_factory=dict)
    environmental_features: Dict[str, float] = field(default_factory=dict)
    disease_status: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    collection_date: Optional[str] = None
    phenotype_source: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the sample to a dictionary representation."""
        return {
            "sample_id": self.sample_id,
            "species": self.species.value,
            "genomic_features": self.genomic_features,
            "environmental_features": self.environmental_features,
            "disease_status": self.disease_status,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "collection_date": self.collection_date,
            "phenotype_source": self.phenotype_source,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Sample":
        """Create a Sample instance from a dictionary."""
        species_str = data.get("species", "").lower()
        try:
            species = Species(species_str)
        except ValueError:
            raise ValueError(f"Unsupported species: {species_str}")

        return cls(
            sample_id=data["sample_id"],
            species=species,
            genomic_features=data.get("genomic_features", {}),
            environmental_features=data.get("environmental_features", {}),
            disease_status=data.get("disease_status"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            collection_date=data.get("collection_date"),
            phenotype_source=data.get("phenotype_source"),
            metadata=data.get("metadata", {})
        )

    def has_valid_label(self) -> bool:
        """Check if the sample has a valid disease status label."""
        return self.disease_status is not None and self.disease_status in (0, 1)

    def has_coordinates(self) -> bool:
        """Check if the sample has valid geographic coordinates."""
        return self.latitude is not None and self.longitude is not None
