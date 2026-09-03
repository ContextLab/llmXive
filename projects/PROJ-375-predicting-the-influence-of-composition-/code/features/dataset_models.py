"""
Pydantic models and validation logic for the Metallic Glass dataset.
Defines the strict schema for data ingestion and feature engineering outputs.
"""
from typing import Optional, Literal, Dict, Any, List
from pydantic import BaseModel, Field, field_validator, ConfigDict, model_validator
from enum import Enum
import re
import math

# Enums for strict typing
class DataSource(str, Enum):
    MATERIALS_PROJECT = "materials_project"
    AFLOW = "aflow"
    ZENODO = "zenodo"

class AlloyFamily(str, Enum):
    # Common metallic glass families
    ZR = "Zr"
    PD = "Pd"
    FE = "Fe"
    MG = "Mg"
    TI = "Ti"
    CU = "Cu"
    OTHER = "Other"

class MetallicGlassEntry(BaseModel):
    """
    Represents a single validated entry in the metallic glass dataset.
    Corresponds to the schema in contracts/mg_dataset.schema.yaml.
    """
    model_config = ConfigDict(strict=True, populate_by_name=True)

    composition: str = Field(..., description="Chemical formula (e.g., 'Zr50Cu40Al10')")
    cte: float = Field(..., ge=0.0, description="Coefficient of Thermal Expansion (1/K)")
    amorphous_flag: bool = Field(..., description="True if confirmed amorphous")
    
    # Derived descriptors
    mean_atomic_radius: float = Field(..., ge=0.0, description="Weighted mean atomic radius (pm)")
    electronegativity_var: float = Field(..., ge=0.0, description="Electronegativity variance")
    vec: float = Field(..., description="Valence Electron Concentration")
    size_mismatch: float = Field(..., ge=0.0, le=1.0, description="Atomic size mismatch parameter")

    # Metadata
    source: DataSource = Field(..., description="Data source")
    alloy_family: AlloyFamily = Field(..., description="Primary alloy family")

    @field_validator('composition')
    @classmethod
    def validate_composition_format(cls, v: str) -> str:
        """
        Validates that the composition string follows standard chemical formula notation.
        Pattern: Element followed by optional number, repeated.
        """
        if not v:
            raise ValueError("Composition cannot be empty")
        # Basic regex for chemical formulas (Element + optional number)
        pattern = r"^[A-Z][a-z]?[0-9.]+([A-Z][a-z]?[0-9.]+)*$"
        if not re.match(pattern, v):
            raise ValueError(f"Invalid chemical formula format: {v}")
        return v

    @field_validator('cte', 'mean_atomic_radius', 'electronegativity_var', 'vec', 'size_mismatch')
    @classmethod
    def check_finite_non_nan(cls, v: float) -> float:
        if math.isnan(v) or math.isinf(v):
            raise ValueError(f"Value must be finite and not NaN: {v}")
        return v

    @model_validator(mode='after')
    def check_amorphous_requirement(self) -> 'MetallicGlassEntry':
        """
        Ensures that only amorphous entries are valid in the final dataset.
        """
        if not self.amorphous_flag:
            raise ValueError("Only amorphous entries (amorphous_flag=True) are allowed in this model.")
        return self

def validate_entry_to_model(entry_dict: Dict[str, Any]) -> MetallicGlassEntry:
    """
    Validates a raw dictionary entry against the MetallicGlassEntry Pydantic model.
    Raises ValueError if validation fails, providing specific error messages.
    
    Args:
        entry_dict: Dictionary containing raw data fields.
        
    Returns:
        Validated MetallicGlassEntry object.
        
    Raises:
        ValueError: If the entry does not match the schema or constraints.
    """
    try:
        # Normalize source string if present
        if 'source' in entry_dict and isinstance(entry_dict['source'], str):
            try:
                entry_dict['source'] = DataSource(entry_dict['source'])
            except ValueError:
                raise ValueError(f"Invalid source value: {entry_dict['source']}")
        
        # Normalize alloy_family string if present
        if 'alloy_family' in entry_dict and isinstance(entry_dict['alloy_family'], str):
            try:
                entry_dict['alloy_family'] = AlloyFamily(entry_dict['alloy_family'])
            except ValueError:
                # Fallback to OTHER if not a recognized family, or raise error depending on strictness
                # Per schema, we expect specific families, but 'Other' is allowed
                if entry_dict['alloy_family'] not in [f.value for f in AlloyFamily]:
                     raise ValueError(f"Invalid alloy_family: {entry_dict['alloy_family']}")
                entry_dict['alloy_family'] = AlloyFamily(entry_dict['alloy_family'])

        return MetallicGlassEntry(**entry_dict)
    except ValueError as e:
        # Re-raise with context if needed, or just propagate
        raise ValueError(f"Validation failed for entry {entry_dict.get('composition', 'unknown')}: {e}")
    except Exception as e:
        raise ValueError(f"Unexpected error validating entry: {e}")
