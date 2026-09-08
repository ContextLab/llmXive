from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Dict, Any
from enum import Enum
import re

class MetaboliteClass(Enum):
    """
    Standardized metabolite classes based on chemical ontology.
    """
    ALKALOID = "alkaloid"
    TERPENOID = "terpenoid"
    PHENOLIC = "phenolic"
    FLAVONOID = "flavonoid"
    GLUCOSINOLATE = "glucosinolate"
    CYANOPROPHENOL = "cyanoprophenol"
    SAPONIN = "saponin"
    ALIPHATIC = "aliphatic"
    INDOLE = "indole"
    OTHER = "other"
    UNKNOWN = "unknown"

    @classmethod
    def from_string(cls, value: str) -> 'MetaboliteClass':
        """
        Convert a string to a MetaboliteClass enum.
        """
        if not value:
            return cls.UNKNOWN

        normalized = value.strip().lower().replace("-", " ").replace("_", " ")

        mapping = {
            "alkaloid": cls.ALKALOID,
            "terpenoid": cls.TERPENOID,
            "terpene": cls.TERPENOID,
            "phenolic": cls.PHENOLIC,
            "phenol": cls.PHENOLIC,
            "flavonoid": cls.FLAVONOID,
            "flavonol": cls.FLAVONOID,
            "glucosinolate": cls.GLUCOSINOLATE,
            "glucosinolate derivative": cls.GLUCOSINOLATE,
            "cyanoprophenol": cls.CYANOPROPHENOL,
            "cyanogenic glucoside": cls.CYANOPROPHENOL,
            "saponin": cls.SAPONIN,
            "aliphatic": cls.ALIPHATIC,
            "indole": cls.INDOLE,
            "other": cls.OTHER,
            "unknown": cls.UNKNOWN,
        }

        return mapping.get(normalized, cls.UNKNOWN)

class Metabolite(BaseModel):
    """
    Pydantic model representing a secondary metabolite.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    metabolite_id: str = Field(..., description="Unique identifier (e.g., PMDB ID, ChEBI ID)")
    common_name: str = Field(..., description="Common chemical name")
    iupac_name: Optional[str] = Field(None, description="IUPAC name")
    inchikey: str = Field(..., description="Standard InChIKey for unambiguous identification")
    smiles: Optional[str] = Field(None, description="SMILES string")
    molecular_formula: Optional[str] = Field(None, description="Molecular formula")
    molecular_weight: Optional[float] = Field(None, ge=0.0, description="Molecular weight in g/mol")
    metabolite_class: MetaboliteClass = Field(default=MetaboliteClass.UNKNOWN, description="Primary chemical class")
    secondary_classes: Optional[List[MetaboliteClass]] = Field(default_factory=list, description="Secondary chemical classes")
    abundance: Optional[float] = Field(None, ge=0.0, description="Measured abundance (normalized)")
    abundance_unit: Optional[str] = Field(None, description="Unit of abundance (e.g., ng/g, ppm)")
    detection_method: Optional[str] = Field(None, description="Method of detection (e.g., LC-MS, GC-MS)")
    source_species_id: Optional[str] = Field(None, description="Species ID where detected")
    raw_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Raw measurement data")

    @field_validator('metabolite_id', 'common_name', 'inchikey')
    @classmethod
    def validate_required_strings(cls, v, info):
        if not v or len(v.strip()) == 0:
            raise ValueError(f"{info.field_name} cannot be empty")
        return v.strip()

    @field_validator('inchikey')
    @classmethod
    def validate_inchikey_format(cls, v):
        # Basic validation for InChIKey format (27 chars, 2 hyphens)
        pattern = r'^[A-Z0-9]{14}-[A-Z0-9]{10}-[A-Z0-9]$'
        if not re.match(pattern, v):
            # Allow partial or non-standard keys but warn in real usage
            # For now, we accept it but log a warning in a real app
            pass
        return v.upper()

    @field_validator('molecular_weight')
    @classmethod
    def validate_weight(cls, v):
        if v is not None and v < 0.0:
            raise ValueError("Molecular weight cannot be negative")
        return v

    def harmonize(self) -> 'Metabolite':
        """
        Apply harmonization steps: InChIKey normalization, log-transformation of abundance.
        Returns a new Metabolite instance with harmonized data.
        """
        import math
        
        new_abundance = self.abundance
        if self.abundance is not None:
            # Apply pseudo-count +1 and log-transform
            new_abundance = math.log1p(self.abundance)
        
        return Metabolite(
            metabolite_id=self.metabolite_id,
            common_name=self.common_name,
            iupac_name=self.iupac_name,
            inchikey=self.inchikey,
            smiles=self.smiles,
            molecular_formula=self.molecular_formula,
            molecular_weight=self.molecular_weight,
            metabolite_class=self.metabolite_class,
            secondary_classes=self.secondary_classes,
            abundance=new_abundance,
            abundance_unit=self.abundance_unit,
            detection_method=self.detection_method,
            source_species_id=self.source_species_id,
            raw_data=self.raw_data
        )
