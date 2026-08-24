from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from datetime import datetime


@dataclass
class RNASeqSample:
    """
    Represents a single RNA-seq sample for the evolutionary pressure analysis.

    Attributes:
        accession_id: Unique identifier for the sample (e.g., SRA accession).
        species: Species name (e.g., 'Homo_sapiens', 'Pan_troglodytes').
        fastq_path: Path to the FASTQ file (local or remote).
        replicate_group: Identifier for the biological replicate group.
        created_at: Timestamp of object creation.
    """
    accession_id: str
    species: str
    fastq_path: str
    replicate_group: str
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

        # Validate path if it looks like a local path
        if self.fastq_path and not self.fastq_path.startswith(('http://', 'https://', 'sra://')):
            path_obj = Path(self.fastq_path)
            if not path_obj.exists():
                # We do not raise here to allow for lazy evaluation or remote paths,
                # but we could log a warning if strict local validation is required.
                pass

    def to_dict(self) -> dict:
        """Convert the sample to a dictionary representation."""
        return {
            'accession_id': self.accession_id,
            'species': self.species,
            'fastq_path': str(self.fastq_path),
            'replicate_group': self.replicate_group,
            'created_at': self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'RNASeqSample':
        """Create an RNASeqSample instance from a dictionary."""
        created_at = data.get('created_at')
        if created_at:
            created_at = datetime.fromisoformat(created_at)
        return cls(
            accession_id=data['accession_id'],
            species=data['species'],
            fastq_path=data['fastq_path'],
            replicate_group=data['replicate_group'],
            created_at=created_at
        )
