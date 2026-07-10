"""
Pydantic model for Metabolite entities.
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
from enum import Enum
import re

class MetaboliteClass(str, Enum):
    """Classification of metabolites based on chemical structure or pathway."""
    ALKALOIDS = "alkaloids"
    TERPENOIDS = "terpenoids"
    PHENYLPROPANOIDS = "phenylpropanoids"
    GLYCOSIDES = "glycosides"
    POLYKETIDES = "polyketides"
    LIPIDS = "lipids"
    OTHER = "other"
    UNKNOWN = "unknown"

class Metabolite(BaseModel):
    """
    Represents a detected metabolite.

    Attributes:
        metabolite_id: Unique identifier for the metabolite.
        inchi_key: Standard InChIKey for unambiguous identification.
        iupac_name: IUPAC chemical name.
        common_name: Common name if available.
        chemical_class: Broad chemical classification.
        abundance: Measured abundance (e.g., peak area, concentration).
        units: Unit of measurement.
        source_db: Database source (e.g., PMDB, MetaboLights).
    """
    model_config = ConfigDict(from_attributes=True)

    metabolite_id: str = Field(..., description="Unique metabolite identifier")
    inchi_key: str = Field(..., description="InChIKey")
    iupac_name: Optional[str] = Field(None, description="IUPAC name")
    common_name: Optional[str] = Field(None, description="Common name")
    chemical_class: MetaboliteClass = Field(default=MetaboliteClass.UNKNOWN, description="Chemical class")
    abundance: float = Field(..., description="Measured abundance", ge=0.0)
    units: Optional[str] = Field(None, description="Measurement units")
    source_db: Optional[str] = Field(None, description="Source database")

    @field_validator('inchi_key')
    @classmethod
    def validate_inchi_key(cls, v: str) -> str:
        """Validate InChIKey format (27 characters, 2 parts separated by hyphen)."""
        if not v:
            return v
        # Standard InChIKey is 27 chars: 14-10-1 with 2 hyphens
        pattern = r'^[A-Z0-9]{14}-[A-Z0-9]{10}-[A-Z0-9]$'
        if not re.match(pattern, v):
            # Allow standard format without the last character if it's a variant, but strict check preferred
            # For now, let's be lenient but warn if it looks wrong, or just accept if it's not empty
            # Strict validation:
            if len(v) != 27 or v.count('-') != 2:
                raise ValueError(f"Invalid InChIKey format: {v}")
        return v

    def log_transform(self, pseudo_count: float = 1.0) -> float:
        """Return log-transformed abundance with pseudo-count."""
        import math
        return math.log(self.abundance + pseudo_count)
