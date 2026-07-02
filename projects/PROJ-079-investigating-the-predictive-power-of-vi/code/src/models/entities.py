"""
Pydantic dataclasses for core research entities.

Defines strict schemas for:
- ViralGenome: Metadata and sequence data for viral genomes.
- HostExpressionSample: Host transcriptomic data with ISG scores.
"""
from dataclasses import dataclass as std_dataclass
from typing import Dict, Any, Optional, List
from pydantic.dataclasses import dataclass as pydantic_dataclass
from pydantic import Field, field_validator, ValidationError
from datetime import datetime
import json

@pydantic_dataclass
class ViralGenome:
    """
    Represents a viral genome entry.

    Attributes:
        accession: Unique identifier (e.g., NCBI RefSeq accession).
        family: Viral family classification (e.g., 'Coronaviridae').
        fasta: The raw FASTA formatted sequence string (header + sequence).
    """
    accession: str = Field(..., description="Unique viral accession identifier")
    family: str = Field(..., description="Viral family classification")
    fasta: str = Field(..., description="Raw FASTA formatted sequence")

    @field_validator('accession')
    @classmethod
    def validate_accession(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValueError("Accession must be a non-empty string")
        return v.strip()

    @field_validator('family')
    @classmethod
    def validate_family(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValueError("Family must be a non-empty string")
        return v.strip()

    @field_validator('fasta')
    @classmethod
    def validate_fasta(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValueError("FASTA content must be a non-empty string")
        # Basic check for FASTA header start
        if not v.startswith('>'):
            raise ValueError("FASTA content must start with a '>' header character")
        return v

    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataclass instance to a dictionary."""
        return {
            "accession": self.accession,
            "family": self.family,
            "fasta": self.fasta
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ViralGenome':
        """Create an instance from a dictionary."""
        return cls(**data)

@pydantic_dataclass
class HostExpressionSample:
    """
    Represents a host gene expression sample.

    Attributes:
        sample_id: Unique identifier for the sample.
        counts: Dictionary mapping gene IDs/symbols to raw count values.
        metadata: Dictionary of sample metadata (e.g., tissue, condition, species).
        isg_score: Calculated Interferon-Stimulated Gene score (optional).
    """
    sample_id: str = Field(..., description="Unique sample identifier")
    counts: Dict[str, Any] = Field(default_factory=dict, description="Gene expression counts")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Sample metadata")
    isg_score: Optional[float] = Field(None, description="Calculated ISG score")

    @field_validator('sample_id')
    @classmethod
    def validate_sample_id(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValueError("Sample ID must be a non-empty string")
        return v.strip()

    @field_validator('counts')
    @classmethod
    def validate_counts(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(v, dict):
            raise ValueError("Counts must be a dictionary")
        # Ensure values are numeric
        for k, val in v.items():
            if not isinstance(val, (int, float)):
                raise ValueError(f"Count value for gene '{k}' must be numeric, got {type(val)}")
        return v

    @field_validator('metadata')
    @classmethod
    def validate_metadata(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(v, dict):
            raise ValueError("Metadata must be a dictionary")
        return v

    @field_validator('isg_score')
    @classmethod
    def validate_isg_score(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if not isinstance(v, (int, float)):
                raise ValueError("ISG score must be a float or None")
            if not (-float('inf') < v < float('inf')):
                raise ValueError("ISG score must be a finite number")
        return v

    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataclass instance to a dictionary."""
        return {
            "sample_id": self.sample_id,
            "counts": self.counts,
            "metadata": self.metadata,
            "isg_score": self.isg_score
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HostExpressionSample':
        """Create an instance from a dictionary."""
        return cls(**data)