"""
Pydantic models for Metabolites.
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
from enum import Enum
import re

class MetaboliteClass(str, Enum):
    """
    Metabolite classes mapped from MIBiG ontology or PMDB.
    """
    ALKALOIDS = "alkaloids"
    TERPENOIDS = "terpenoids"
    PHENYLPROPANOIDS = "phenylpropanoids"
    GLUCOSINOLATES = "glucosinolates"
    GLYCOSIDES = "glycosides"
    LIPIDS = "lipids"
    AMINO_ACIDS_DERIVATIVES = "amino acids derivatives"
    OTHER = "other"
    UNKNOWN = "unknown"

class Metabolite(BaseModel):
    """
    Represents a metabolite entry with abundance data.
    """
    model_config = ConfigDict(from_attributes=True)

    metabolite_id: str = Field(..., description="Unique metabolite identifier (e.g., PMDB ID)")
    inchi_key: str = Field(..., description="InChIKey for unambiguous identification")
    chemical_name: str = Field(..., description="Common chemical name")
    metabolite_class: MetaboliteClass = Field(..., description="Primary chemical class")
    species_id: str = Field(..., description="Reference to the species")
    abundance_value: float = Field(..., ge=0.0, description="Raw abundance value")
    abundance_unit: Optional[str] = Field(None, description="Unit of measurement")
    detection_method: Optional[str] = Field(None, description="Detection method (e.g., LC-MS, NMR)")
    pmdb_id: Optional[str] = Field(None, description="Original PMDB ID if applicable")
    metabololights_id: Optional[str] = Field(None, description="MetaboLights study ID if applicable")
    log_transformed: bool = Field(False, description="Whether log transformation has been applied")

    @field_validator("inchi_key")
    @classmethod
    def validate_inchi_key(cls, v: str) -> str:
        """Validate InChIKey format (27 characters, two blocks separated by hyphen)."""
        if not v:
            return v
        # Basic InChIKey format check: 14 chars - 10 chars - 1 char
        pattern = r"^[A-Z0-9]{14}-[A-Z0-9]{10}-[A-Z0-9]$"
        if not re.match(pattern, v):
            raise ValueError(f"Invalid InChIKey format: {v}")
        return v
