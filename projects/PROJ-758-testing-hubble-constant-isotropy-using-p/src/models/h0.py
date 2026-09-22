"""
Pydantic model for Hubble Constant (H0) estimates.

Defines the schema for H0 measurements derived from supernova samples,
including global and local (pixel-based) estimates.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime

class H0Estimate(BaseModel):
    """
    Represents a single H0 estimate derived from a supernova sample.

    Attributes:
        estimate_id: Unique identifier for this estimate
        pixel_id: HEALPix pixel index (None for global estimate)
        nside: HEALPix resolution parameter (None for global)
        supernova_count: Number of supernovae used in the fit
        h_value: Estimated H0 value (km/s/Mpc)
        h0_error: Standard error on H0 estimate
        method: Estimation method (e.g., 'linear', 'nonlinear', 'hierarchical')
        redshift_min: Minimum redshift of sample
        redshift_max: Maximum redshift of sample
        chi2: Chi-squared of the fit
        dof: Degrees of freedom
        timestamp: Timestamp of calculation
        is_local: True if this is a local (pixel) estimate
        is_valid: True if estimate meets quality criteria
    """
    estimate_id: str = Field(..., description="Unique estimate identifier")
    pixel_id: Optional[int] = Field(None, description="HEALPix pixel index (None for global)")
    nside: Optional[int] = Field(None, description="HEALPix Nside (None for global)")
    supernova_count: int = Field(..., ge=1, description="Number of supernovae")
    h_value: float = Field(..., gt=0.0, description="H0 estimate (km/s/Mpc)")
    h0_error: float = Field(..., gt=0.0, description="Standard error")
    method: str = Field(..., description="Estimation method")
    redshift_min: float = Field(..., gt=0.0, description="Min redshift")
    redshift_max: float = Field(..., gt=0.0, description="Max redshift")
    chi2: float = Field(..., ge=0.0, description="Chi-squared statistic")
    dof: int = Field(..., gt=0, description="Degrees of freedom")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Calculation time")
    is_local: bool = Field(..., description="Is this a local estimate?")
    is_valid: bool = Field(..., description="Does it meet quality criteria?")

    @field_validator('h_value')
    @classmethod
    def validate_h_value(cls, v):
        if v <= 0:
            raise ValueError("H0 value must be positive")
        return v

    @field_validator('h0_error')
    @classmethod
    def validate_h0_error(cls, v):
        if v <= 0:
            raise ValueError("H0 error must be positive")
        return v

    @field_validator('redshift_min', 'redshift_max')
    @classmethod
    def validate_redshift(cls, v):
        if v <= 0:
            raise ValueError("Redshift must be positive")
        return v

    @field_validator('chi2')
    @classmethod
    def validate_chi2(cls, v):
        if v < 0:
            raise ValueError("Chi-squared cannot be negative")
        return v

    @field_validator('dof')
    @classmethod
    def validate_dof(cls, v):
        if v <= 0:
            raise ValueError("Degrees of freedom must be positive")
        return v

    @field_validator('pixel_id')
    @classmethod
    def validate_pixel_consistency(cls, v, info):
        """Ensure pixel_id and is_local are consistent."""
        is_local = info.data.get('is_local')
        if is_local and v is None:
            raise ValueError("Local estimates must have a pixel_id")
        if not is_local and v is not None:
            raise ValueError("Global estimates should not have a pixel_id")
        return v

    @field_validator('nside')
    @classmethod
    def validate_nside_consistency(cls, v, info):
        """Ensure nside and is_local are consistent."""
        is_local = info.data.get('is_local')
        if is_local and v is None:
            raise ValueError("Local estimates must have an nside")
        if not is_local and v is not None:
            raise ValueError("Global estimates should not have an nside")
        return v
