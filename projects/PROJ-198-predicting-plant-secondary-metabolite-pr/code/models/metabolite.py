"""
Pydantic models for Metabolites.
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
from enum import Enum
import re


class MetaboliteClass(str, Enum):
    """
    Enum for known metabolite classes based on MIBiG 3.0 ontology.
    """
    POLYKETIDE = "polyketide"
    NON_RIBOSOMAL_PEPTIDE = "non-ribosomal peptide"
    TERPENE = "terpene"
    ALKALOID = "alkaloid"
    RIBOSOMALLY_SYNTHESIZED_AND_POST_TRANSLATIONALLY_MODIFIED_PEPTIDE = "ribo-synthetically modified peptide"
    SACCHARIDE = "saccharide"
    OTHER = "other"
    UNKNOWN = "unknown"


class Metabolite(BaseModel):
    """
    Model representing a single metabolite detected in a species.
    """
    model_config = ConfigDict(use_enum_values=True, populate_by_name=True)

    species_id: str = Field(..., description="Unique identifier for the species")
    metabolite_id: str = Field(..., description="Unique identifier for the metabolite (e.g., PMDB ID)")
    inchi_key: str = Field(..., description="InChIKey for the metabolite")
    name: Optional[str] = Field(None, description="Common name of the metabolite")
    metabolite_class: MetaboliteClass = Field(
        ...,
        description="Class of the metabolite"
    )
    abundance: float = Field(
        ...,
        ge=0.0,
        description="Measured abundance (e.g., peak area, concentration)"
    )
    detection_method: Optional[str] = Field(None, description="Method used for detection (e.g., LC-MS)")
    confidence_level: Optional[str] = Field(None, description="Confidence level of identification")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")

    @field_validator('inchi_key')
    @classmethod
    def validate_inchi_key(cls, v: str) -> str:
        """Validate that the InChIKey matches the standard format (27 characters, two blocks separated by hyphen)."""
        if not v:
            raise ValueError("InChIKey cannot be empty")
        # Standard InChIKey format: 14 chars - 10 chars - 1 char (e.g., UHFFFAOYSA-N)
        # Total 27 characters including hyphens.
        pattern = r'^[A-Z0-9]{14}-[A-Z0-9]{10}-[A-Z0-9]$'
        if not re.match(pattern, v):
            raise ValueError(f"Invalid InChIKey format: {v}")
        return v

    @field_validator('abundance')
    @classmethod
    def validate_abundance(cls, v: float) -> float:
        """Ensure abundance is non-negative."""
        if v < 0.0:
            raise ValueError(f"Abundance cannot be negative: {v}")
        return v

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return self.model_dump()

    def to_json(self) -> str:
        """Convert model to JSON string."""
        return self.model_dump_json()
