"""
Pydantic models for metallic glass data schema.
"""
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum

class DataSource(str, Enum):
    MATERIALS_PROJECT = "materials_project"
    AFLOWLIB = "aflowlib"
    ZENODO = "zenodo"

class AlloyFamily(str, Enum):
    ZR = "Zr"
    PD = "Pd"
    FE = "Fe"

class MetallicGlassEntry(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    source: DataSource
    composition: str
    structure_id: str
    nsites: int
    amorphous_state_flag: Optional[bool] = None
    cte_value: Optional[float] = None
    alloy_family: Optional[AlloyFamily] = None

    @field_validator("composition")
    @classmethod
    def validate_composition(cls, v: str) -> str:
        if not v:
            raise ValueError("Composition cannot be empty")
        return v
