"""
Pydantic models for Metabolite data.
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
from enum import Enum
import re

class MetaboliteClass(str, Enum):
    """
    Standardized metabolite classes (e.g., from MIBiG or PMDB).
    """
    ALKALOID = "alkaloid"
    FLAVONOID = "flavonoid"
    TERPENOIDE = "terpenoide"
    PHENYLPROPANOIDS = "phenylpropanoids"
    GLUCOSINOLATE = "glucosinolate"
    ALIPHATIC = "aliphatic"
    INDOLIC = "indolic"
    STEROID = "steroid"
    UNKNOWN = "unknown"

class Metabolite(BaseModel):
    """
    Represents a detected metabolite with abundance data.
    """
    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        str_strip_whitespace=True
    )

    metabolite_id: str = Field(..., description="Unique identifier (e.g., PMDB ID, PubChem CID)")
    inchi_key: str = Field(..., description="Standard InChIKey for unambiguous identification")
    common_name: Optional[str] = Field(None, description="Common chemical name")
    chemical_class: Optional[MetaboliteClass] = Field(None, description="Broad chemical classification")
    species_id: str = Field(..., description="Reference to the source species")
    abundance: float = Field(
        ...,
        ge=0.0,
        description="Measured abundance (e.g., peak area, concentration)"
    )
    abundance_unit: Optional[str] = Field(None, description="Unit of measurement")
    detection_method: Optional[str] = Field(None, description="Method used (e.g., 'LC-MS', 'GC-MS')")
    retention_time: Optional[float] = Field(None, ge=0.0, description="Chromatographic retention time")
    mass_to_charge: Optional[float] = Field(None, description="m/z value")

    @field_validator('inchi_key')
    @classmethod
    def validate_inchi_key(cls, v: str) -> str:
        """
        Validates that the InChIKey is in the standard 27-character format.
        """
        if not v:
            raise ValueError("InChIKey cannot be empty")
        # Standard InChIKey format: 14 chars + hyphen + 10 chars + hyphen + 1 char
        pattern = r"^[A-Z0-9]{14}-[A-Z0-9]{10}-[A-Z0-9]$"
        if not re.match(pattern, v):
            raise ValueError(f"Invalid InChIKey format: {v}. Expected 14-10-1 format.")
        return v
