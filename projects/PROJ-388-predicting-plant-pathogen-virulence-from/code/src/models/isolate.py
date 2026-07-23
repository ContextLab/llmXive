"""
Isolate data model for plant pathogen research.

Defines the Isolate class representing a single pathogen isolate
with genomic and phenotypic data.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class Isolate:
    """
    Represents a single pathogen isolate with genomic and phenotypic data.

    Attributes:
        strain_id: Unique identifier for the isolate strain.
        species: Species name of the pathogen.
        genome_path: Path to the genome assembly file (FASTA/GenBank).
        phenotype_score: Virulence/disease severity score (float).
        metadata: Additional key-value pairs for the isolate.
    """
    strain_id: str
    species: str
    genome_path: str
    phenotype_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate isolate fields after initialization."""
        if not self.strain_id or not isinstance(self.strain_id, str):
            raise ValueError("strain_id must be a non-empty string")
        
        if not self.species or not isinstance(self.species, str):
            raise ValueError("species must be a non-empty string")
        
        if not self.genome_path or not isinstance(self.genome_path, str):
            raise ValueError("genome_path must be a non-empty string")
        
        if not isinstance(self.phenotype_score, (int, float)):
            raise ValueError("phenotype_score must be a numeric value")
        
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a dictionary")

    def to_dict(self) -> Dict[str, Any]:
        """Convert isolate to dictionary representation."""
        return {
            "strain_id": self.strain_id,
            "species": self.species,
            "genome_path": self.genome_path,
            "phenotype_score": self.phenotype_score,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Isolate":
        """Create an Isolate instance from a dictionary."""
        return cls(
            strain_id=data["strain_id"],
            species=data["species"],
            genome_path=data["genome_path"],
            phenotype_score=data["phenotype_score"],
            metadata=data.get("metadata", {})
        )
