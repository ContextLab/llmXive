from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class Isolate:
    """
    Represents a single pathogen isolate with genomic and phenotypic data.

    Fields:
        strain_id: Unique identifier for the isolate strain.
        species: Scientific name of the species.
        genome_path: Path to the genome assembly file (e.g., FASTA).
        phenotype_score: Quantitative virulence or disease severity score.
        metadata: Dictionary for additional arbitrary attributes.
    """
    strain_id: str
    species: str
    genome_path: str
    phenotype_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
