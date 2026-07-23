from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class SpeciesAggregate:
    """
    Aggregated statistics for a plant pathogen species.

    Used when isolate-level linkage is insufficient (<50%), requiring
    analysis at the species level.

    Attributes:
        species_name: The scientific name of the species (e.g., 'Fusarium graminearum').
        avg_phenotype: The mean disease severity score across all isolates of this species.
        isolate_count: The number of distinct isolates included in this aggregate.
        variance: The variance of the phenotypic scores within this species group.
    """
    species_name: str
    avg_phenotype: float
    isolate_count: int
    variance: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert the aggregate to a dictionary representation."""
        return {
            "species_name": self.species_name,
            "avg_phenotype": self.avg_phenotype,
            "isolate_count": self.isolate_count,
            "variance": self.variance
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SpeciesAggregate":
        """Create a SpeciesAggregate instance from a dictionary."""
        return cls(
            species_name=data["species_name"],
            avg_phenotype=data["avg_phenotype"],
            isolate_count=data["isolate_count"],
            variance=data["variance"]
        )
