from typing import Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum
import re

class DataSource(str, Enum):
    """Enum for data source identifiers."""
    MATERIALS_PROJECT = "materials_project"
    AFLOW = "aflow"
    ZENODO = "zenodo"

class AlloyFamily(str, Enum):
    """Enum for alloy family classification."""
    ZR = "Zr"
    PD = "Pd"
    FE = "Fe"
    MG = "Mg"
    TI = "Ti"
    CU = "Cu"
    LA = "La"
    OTHER = "Other"

class MetallicGlassEntry(BaseModel):
    """
    Pydantic model representing a single metallic glass entry.
    
    Attributes:
        composition: Chemical formula (e.g., "Zr50Cu40Al10")
        cte: Coefficient of Thermal Expansion (1e-6 /K)
        weighted_mean_atomic_radius: Weighted mean atomic radius (pm)
        electronegativity_variance: Variance of electronegativity values
        vec: Valence Electron Concentration
        atomic_size_mismatch: Atomic size mismatch parameter (delta)
        amorphous_state_flag: Boolean indicating amorphous state
        source: Origin of the data entry
        alloy_family: Primary alloy family classification
        entry_id: Unique identifier
        metadata: Additional optional metadata
    """
    model_config = ConfigDict(extra='forbid', strict=True)

    composition: str = Field(..., description="Chemical formula in Hill notation")
    cte: float = Field(..., ge=0.0, description="Coefficient of Thermal Expansion (1e-6 /K)")
    weighted_mean_atomic_radius: float = Field(..., ge=0.0, description="Weighted mean atomic radius (pm)")
    electronegativity_variance: float = Field(..., ge=0.0, description="Variance of electronegativity")
    vec: float = Field(..., ge=0.0, description="Valence Electron Concentration")
    atomic_size_mismatch: float = Field(..., ge=0.0, description="Atomic size mismatch parameter")
    amorphous_state_flag: bool = Field(..., description="True if confirmed amorphous")
    source: DataSource = Field(..., description="Data source")
    alloy_family: AlloyFamily = Field(default=AlloyFamily.OTHER, description="Alloy family")
    entry_id: str = Field(..., description="Unique entry ID")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

    @field_validator('composition')
    @classmethod
    def validate_composition_format(cls, v: str) -> str:
        """Validate that composition matches expected formula format."""
        # Basic check for element-number pattern (e.g., Zr50Cu40Al10)
        pattern = r"^[A-Z][a-z]?\d+(\.\d+)?([A-Z][a-z]?\d+(\.\d+)?)*$"
        if not re.match(pattern, v):
            raise ValueError(f"Invalid composition format: {v}. Expected format like 'Zr50Cu40Al10'.")
        return v

    @field_validator('alloy_family')
    @classmethod
    def infer_alloy_family(cls, v: AlloyFamily, info) -> AlloyFamily:
        """Infer alloy family from composition if not explicitly set, 
        but for now we rely on the passed value or default to Other."""
        # This validator could be expanded to infer from composition
        return v

def validate_entry_to_model(entry_dict: dict) -> MetallicGlassEntry:
    """
    Helper function to validate a dictionary against the MetallicGlassEntry model.
    Converts string source values to DataSource enum if necessary.
    """
    if 'source' in entry_dict and isinstance(entry_dict['source'], str):
        try:
            entry_dict['source'] = DataSource(entry_dict['source'])
        except ValueError:
            raise ValueError(f"Invalid source value: {entry_dict['source']}")
    
    if 'alloy_family' in entry_dict and isinstance(entry_dict['alloy_family'], str):
        try:
            entry_dict['alloy_family'] = AlloyFamily(entry_dict['alloy_family'])
        except ValueError:
            raise ValueError(f"Invalid alloy_family value: {entry_dict['alloy_family']}")
    
    return MetallicGlassEntry(**entry_dict)