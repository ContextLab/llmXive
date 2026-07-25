"""
Pydantic model for Species metadata.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class Species(BaseModel):
    """
    Represents a plant species in the study.
    """
    model_config = ConfigDict(from_attributes=True)

    species_id: str = Field(..., description="Unique identifier for the species (e.g., NCBI TaxID)")
    scientific_name: str = Field(..., description="Binomial scientific name")
    common_name: Optional[str] = Field(None, description="Common name if available")
    family: Optional[str] = Field(None, description="Plant family")
    assembly_accession: Optional[str] = Field(None, description="Genomic assembly accession (e.g., GCA_...)")
    genome_size_bp: Optional[int] = Field(None, description="Estimated genome size in base pairs")
    download_status: Optional[str] = Field("pending", description="Status of genome download (pending, downloaded, failed)")
    download_path: Optional[str] = Field(None, description="Path to downloaded genome files")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
