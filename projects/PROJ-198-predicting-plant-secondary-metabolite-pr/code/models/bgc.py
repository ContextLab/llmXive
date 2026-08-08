"""
Pydantic models for BGC (Biosynthetic Gene Cluster) features.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from enum import Enum
import json


class BGCType(str, Enum):
    """
    Enum for known BGC types based on MIBiG 3.0 ontology.
    """
    POLYKETIDE = "polyketide"
    NON_RIBOSOMAL_PEPTIDE = "non-ribosomal peptide"
    TERPENE = "terpene"
    ALKALOID = "alkaloid"
    RIBOSOMALLY_SYNTHESIZED_AND_POST_TRANSLATIONALLY_MODIFIED_PEPTIDE = "ribo-synthetically modified peptide"
    SACCHARIDE = "saccharide"
    OTHER = "other"
    UNKNOWN = "unknown"


class BGCFeature(BaseModel):
    """
    Model representing a single BGC feature detected in a species.
    """
    model_config = ConfigDict(use_enum_values=True, populate_by_name=True)

    species_id: str = Field(..., description="Unique identifier for the species")
    bgc_id: str = Field(..., description="Unique identifier for the BGC cluster")
    bgc_type: BGCType = Field(..., description="Type of the BGC cluster")
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score from the detection tool (e.g., antiSMASH)"
    )
    start_position: int = Field(..., ge=0, description="Start position in the genome assembly")
    end_position: int = Field(..., ge=0, description="End position in the genome assembly")
    gene_count: Optional[int] = Field(None, ge=0, description="Number of genes in the cluster")
    source_tool: Optional[str] = Field("antiSMASH", description="Tool used to detect this BGC")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")

    @property
    def length(self) -> int:
        """Calculate the length of the BGC region."""
        return max(0, self.end_position - self.start_position)

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return self.model_dump()

    def to_json(self) -> str:
        """Convert model to JSON string."""
        return self.model_dump_json()
