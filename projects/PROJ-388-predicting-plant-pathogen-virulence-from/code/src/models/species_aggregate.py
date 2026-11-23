"""
Module defining the SpeciesAggregate data model.

This class represents aggregated statistics for a specific plant pathogen species,
derived from multiple isolates. It is used when isolate-level phenotype linkage
is insufficient (fallback logic in merge.py).
"""
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class SpeciesAggregate:
    """
    Aggregated data for a single plant pathogen species.

    Attributes:
        species_name (str): The scientific name of the species (e.g., 'Fusarium graminearum').
        avg_phenotype (float): The mean phenotypic disease severity score for this species.
        isolate_count (int): The number of distinct isolates contributing to this aggregate.
        variance (float): The variance of the phenotypic scores across the isolates.
        metadata (Dict[str, Any], optional): Additional context (e.g., data sources, aggregation method).
    """
    species_name: str
    avg_phenotype: float
    isolate_count: int
    variance: float
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        """Validate that isolate_count is positive and scores are numeric."""
        if self.isolate_count <= 0:
            raise ValueError(f"isolate_count must be positive, got {self.isolate_count}")
        if not isinstance(self.avg_phenotype, (int, float)):
            raise TypeError(f"avg_phenotype must be numeric, got {type(self.avg_phenotype)}")
        if not isinstance(self.variance, (int, float)):
            raise TypeError(f"variance must be numeric, got {type(self.variance)}")
        if self.variance < 0:
            raise ValueError(f"variance cannot be negative, got {self.variance}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert the instance to a dictionary for serialization."""
        base = {
            "species_name": self.species_name,
            "avg_phenotype": self.avg_phenotype,
            "isolate_count": self.isolate_count,
            "variance": self.variance,
        }
        if self.metadata:
            base["metadata"] = self.metadata
        return base

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SpeciesAggregate":
        """Construct an instance from a dictionary."""
        return cls(
            species_name=data["species_name"],
            avg_phenotype=data["avg_phenotype"],
            isolate_count=data["isolate_count"],
            variance=data["variance"],
            metadata=data.get("metadata"),
        )
