"""
Pydantic models for species data.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class Species(BaseModel):
    """Model representing a plant species."""
    model_config = ConfigDict(extra='forbid')
    
    species_id: str = Field(..., description="Unique identifier for the species")
    scientific_name: str = Field(..., description="Scientific name (e.g., Arabidopsis thaliana)")
    common_name: Optional[str] = Field(None, description="Common name if available")
    family: Optional[str] = Field(None, description="Taxonomic family")
    genome_size_bp: Optional[int] = Field(None, description="Genome size in base pairs")
    assembly_accession: Optional[str] = Field(None, description="NCBI Assembly accession")
    created_at: Optional[datetime] = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default_factory=datetime.now, description="Last update timestamp")

    def __str__(self) -> str:
        return f"{self.species_id}: {self.scientific_name}"
