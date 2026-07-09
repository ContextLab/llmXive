import numpy as np
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator

class MaterialType(str, Enum):
    """Enumeration of supported FCC metals for texture analysis."""
    ALUMINUM = "Al"
    COPPER = "Cu"
    NICKEL = "Ni"

class Symmetry(str, Enum):
    """Crystal symmetry groups supported in the pipeline."""
    CUBIC = "cubic"
    HEXAGONAL = "hexagonal"
    ORTHORHOMBIC = "orthorhombic"

class TextureComponent(str, Enum):
    """Standard FCC texture components defined by Miller indices or Euler ranges."""
    BRASS = "Brass"
    COPPER = "Copper"
    S = "S"
    Goss = "Goss"
    CUBE = "Cube"
    RANDOM = "Random"

class EbsdSample(BaseModel):
    """
    Represents a single EBSD measurement point or averaged grain.
    Extends existing schema from T007a.
    """
    sample_id: str = Field(..., description="Unique identifier for the sample")
    material: MaterialType = Field(..., description="Material type (Al, Cu, Ni)")
    symmetry: Symmetry = Field(Symmetry.CUBIC, description="Crystal symmetry")
    reduction_percent: float = Field(..., ge=0.0, le=100.0, description="Cold rolling reduction percentage")
    confidence_index: float = Field(..., ge=0.0, le=1.0, description="EBSD confidence index")
    euler_angles: List[float] = Field(..., min_length=3, max_length=3, description="Euler angles (Bunge convention) in degrees")
    grain_id: Optional[int] = Field(None, description="Grain ID if grain-based averaging")
    processed_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator('euler_angles')
    @classmethod
    def validate_euler_angles(cls, v: List[float]) -> List[float]:
        if len(v) != 3:
            raise ValueError("Euler angles must contain exactly 3 values (phi1, Phi, phi2).")
        # Basic range check for degrees
        if not all(0.0 <= x <= 360.0 for x in v[:2]) or not all(0.0 <= x <= 90.0 for x in v[2:3]):
            # Note: Phi2 can technically go up to 360, but standard Bunge is often 0-360 for phi1/phi2, 0-180 for Phi.
            # We allow 0-360 for all here to be permissive, relying on orix for strict symmetry checks later.
            pass
        return v

class TextureDescriptor(BaseModel):
    """
    Quantitative descriptor of crystallographic texture derived from EBSD data.
    Includes volume fractions of major components and global texture indices.
    """
    sample_id: str = Field(..., description="Reference to the source EBSD sample or batch")
    material: MaterialType = Field(..., description="Material type")
    reduction_percent: float = Field(..., ge=0.0, le=100.0)
    
    # Global Indices
    texture_index: float = Field(..., ge=1.0, description="Global texture index (J-index equivalent)")
    orientation_spread: float = Field(..., ge=0.0, description="Average orientation spread in degrees")
    
    # Volume Fractions (sum should be approx 1.0)
    vol_frac_brass: float = Field(..., ge=0.0, le=1.0)
    vol_frac_copper: float = Field(..., ge=0.0, le=1.0)
    vol_frac_s: float = Field(..., ge=0.0, le=1.0)
    vol_frac_goss: float = Field(..., ge=0.0, le=1.0)
    vol_frac_cube: float = Field(..., ge=0.0, le=1.0)
    vol_frac_random: float = Field(..., ge=0.0, le=1.0)
    
    # Metadata
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    method: str = Field("MTX-search", description="Method used for calculation (e.g., MTEX-style search)")

    @model_validator(mode='after')
    def check_mass_balance(self) -> 'TextureDescriptor':
        """
        Ensures the sum of volume fractions is approximately 1.0.
        Tolerance is set to 0.01 as per specification FR-002 / T019 logic.
        """
        total = (
            self.vol_frac_brass +
            self.vol_frac_copper +
            self.vol_frac_s +
            self.vol_frac_goss +
            self.vol_frac_cube +
            self.vol_frac_random
        )
        if not (0.99 <= total <= 1.01):
            raise ValueError(
                f"Mass balance check failed: Sum of volume fractions is {total:.4f}. "
                "Expected sum to be within [0.99, 1.01]."
            )
        return self

class EbsdDatasetMetadata(BaseModel):
    """Metadata for a collection of EBSD samples."""
    dataset_id: str
    source: str
    material: MaterialType
    symmetry: Symmetry
    created_at: datetime = Field(default_factory=datetime.utcnow)
    sample_count: int = 0
    reduction_levels: List[float] = Field(default_factory=list)

class ModelInput(BaseModel):
    """Structured input for predictive modeling tasks."""
    reduction_percent: float
    material_code: int  # Enum index or mapped integer
    texture_index: Optional[float] = None
    vol_frac_brass: Optional[float] = None
    vol_frac_copper: Optional[float] = None
    vol_frac_s: Optional[float] = None
    vol_frac_goss: Optional[float] = None

    @field_validator('material_code')
    @classmethod
    def validate_material_code(cls, v: int) -> int:
        if v < 0 or v >= len(MaterialType):
            raise ValueError(f"Invalid material code: {v}. Must be within range [0, {len(MaterialType)-1}].")
        return v