"""
Pydantic model for Species entities.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class Species(BaseModel):
    """
    Represents a plant species in the study.

    Attributes:
        species_id: Unique identifier for the species (e.g., NCBI TaxID or custom slug).
        scientific_name: Validated binomial name.
        common_name: Optional common name.
        assembly_accession: Accession number for the genomic assembly (e.g., GCF_...).
        assembly_version: Version string of the assembly.
        genome_size_bp: Genome size in base pairs.
        source_db: Database where the genome was sourced from (e.g., 'RefSeq', 'Phytozome').
        download_timestamp: Timestamp when the data was downloaded.
    """
    model_config = ConfigDict(from_attributes=True)

    species_id: str = Field(..., description="Unique species identifier")
    scientific_name: str = Field(..., description="Binomial scientific name")
    common_name: Optional[str] = Field(None, description="Common name")
    assembly_accession: str = Field(..., description="Genomic assembly accession")
    assembly_version: str = Field(..., description="Assembly version")
    genome_size_bp: int = Field(..., description="Genome size in base pairs", gt=0)
    source_db: str = Field(..., description="Source database")
    download_timestamp: Optional[datetime] = Field(None, description="Download timestamp")

    def is_large_genome(self, threshold_mb: int = 500) -> bool:
        """Check if the genome exceeds a size threshold in MB."""
        return self.genome_size_bp > (threshold_mb * 1_000_000)
