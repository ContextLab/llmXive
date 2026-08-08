"""
Pydantic models for Species.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class Species(BaseModel):
    """
    Model representing a plant species in the study.
    """
    model_config = ConfigDict(populate_by_name=True)

    species_id: str = Field(..., description="Unique identifier for the species (e.g., taxon ID or custom ID)")
    scientific_name: str = Field(..., description="Scientific name (binomial)")
    common_name: Optional[str] = Field(None, description="Common name if available")
    family: Optional[str] = Field(None, description="Taxonomic family")
    genome_assembly_id: Optional[str] = Field(None, description="Genome assembly accession (e.g., NCBI RefSeq)")
    genome_size_mb: Optional[float] = Field(None, ge=0.0, description="Genome size in Megabases")
    chromosome_count: Optional[int] = Field(None, ge=1, description="Number of chromosomes")
    ploidy_level: Optional[int] = Field(None, ge=1, description="Ploidy level (e.g., 2 for diploid)")
    data_sources: Optional[List[str]] = Field(
        default_factory=list,
        description="List of data sources for this species (e.g., 'NCBI', 'Phytozome')"
    )
    download_date: Optional[datetime] = Field(None, description="Date when data was downloaded")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return self.model_dump()

    def to_json(self) -> str:
        """Convert model to JSON string."""
        return self.model_dump_json()
