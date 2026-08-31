from typing import Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum
import re

class DataSource(str, Enum):
    """Enumeration of data sources."""
    MATERIALS_PROJECT = "Materials Project"
    AFLOWLIB = "AFLOWlib"
    ZENODO = "Zenodo"

class AlloyFamily(str, Enum):
    """Enumeration of alloy families."""
    ZR = "Zr"
    PD = "Pd"
    FE = "Fe"
    MG = "Mg"
    LA = "La"
    TI = "Ti"
    CU = "Cu"
    OTHER = "Other"

class MetallicGlassEntry(BaseModel):
    """Pydantic model for a single metallic glass entry."""
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)

    composition: str = Field(..., description="Chemical formula in Hill order")
    cte: float = Field(..., ge=0.0, description="Coefficient of Thermal Expansion (10^-6 / K)")
    weighted_mean_atomic_radius: float = Field(..., ge=0.0, description="Weighted mean atomic radius (pm)")
    electronegativity_variance: float = Field(..., ge=0.0, description="Variance of electronegativity")
    vec: float = Field(..., ge=0.0, description="Valence Electron Concentration")
    size_mismatch: float = Field(..., ge=0.0, description="Atomic size mismatch parameter")
    amorphous_state: bool = Field(..., description="True if amorphous, False otherwise")
    alloy_family: AlloyFamily = Field(..., description="Primary alloy family")
    source: DataSource = Field(..., description="Source of the data")
    material_id: Optional[str] = Field(None, description="Unique identifier from source")
    formation_energy: Optional[float] = Field(None, ge=-100.0, le=100.0, description="Formation energy (eV/atom)")

    @field_validator('composition')
    @classmethod
    def validate_composition(cls, v: str) -> str:
        """Validate chemical formula format."""
        # Basic regex for chemical formulas (Element followed by optional number)
        pattern = r"^[A-Z][a-z]?[0-9.]+([A-Z][a-z]?[0-9.]+)*$"
        if not re.match(pattern, v):
            raise ValueError(f"Invalid chemical formula format: {v}")
        return v

    @field_validator('alloy_family', mode='before')
    @classmethod
    def normalize_alloy_family(cls, v: Any) -> AlloyFamily:
        """Normalize alloy family string to enum."""
        if isinstance(v, str):
            v = v.strip().upper()
            mapping = {
                "ZR": AlloyFamily.ZR,
                "PALLADIUM": AlloyFamily.PD,
                "PD": AlloyFamily.PD,
                "FE": AlloyFamily.FE,
                "IRON": AlloyFamily.FE,
                "MG": AlloyFamily.MG,
                "MAGNESIUM": AlloyFamily.MG,
                "LA": AlloyFamily.LA,
                "LANTHANUM": AlloyFamily.LA,
                "TI": AlloyFamily.TI,
                "TITANIUM": AlloyFamily.TI,
                "CU": AlloyFamily.CU,
                "COPPER": AlloyFamily.CU,
            }
            if v in mapping:
                return mapping[v]
            return AlloyFamily.OTHER
        return v

    @field_validator('source', mode='before')
    @classmethod
    def normalize_source(cls, v: Any) -> DataSource:
        """Normalize source string to enum."""
        if isinstance(v, str):
            v = v.strip()
            mapping = {
                "materials project": DataSource.MATERIALS_PROJECT,
                "materialsproject": DataSource.MATERIALS_PROJECT,
                "mp": DataSource.MATERIALS_PROJECT,
                "aflow": DataSource.AFLOWLIB,
                "aflowlib": DataSource.AFLOWLIB,
                "zenodo": DataSource.ZENODO,
            }
            lower_v = v.lower()
            if lower_v in mapping:
                return mapping[lower_v]
            raise ValueError(f"Unknown data source: {v}")
        return v

def validate_entry_to_model(entry: Dict[str, Any]) -> MetallicGlassEntry:
    """
    Validate a dictionary entry against the MetallicGlassEntry model.

    Args:
        entry: Dictionary containing metallic glass data.

    Returns:
        Validated MetallicGlassEntry instance.

    Raises:
        ValueError: If validation fails.
    """
    try:
        return MetallicGlassEntry(**entry)
    except Exception as e:
        raise ValueError(f"Failed to validate entry: {e}") from e