"""
Pydantic model for HEALPix pixel representation.

Defines the schema for spatial bins used to partition the sky for
anisotropy analysis.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List

class HEALPixPixel(BaseModel):
    """
    Represents a HEALPix pixel on the celestial sphere.

    Attributes:
        nside: HEALPix resolution parameter (Nside)
        pixel_index: NESTED ordering index for this pixel
        ra_center: Right Ascension of pixel center (degrees)
        dec_center: Declination of pixel center (degrees)
        area_sq_deg: Solid angle of the pixel in square degrees
        supernova_count: Number of supernovae assigned to this pixel
        h0_estimate: Optional H0 estimate for this pixel
        h0_error: Optional error on H0 estimate
        is_valid: Flag indicating if the pixel meets minimum SN count
    """
    nside: int = Field(..., gt=0, description="HEALPix Nside parameter")
    pixel_index: int = Field(..., ge=0, description="NESTED pixel index")
    ra_center: float = Field(..., ge=0.0, le=360.0, description="Center RA (degrees)")
    dec_center: float = Field(..., ge=-90.0, le=90.0, description="Center Dec (degrees)")
    area_sq_deg: float = Field(..., gt=0.0, description="Pixel area in sq degrees")
    supernova_count: int = Field(..., ge=0, description="Number of SNe in pixel")
    h0_estimate: Optional[float] = Field(None, description="Estimated H0 (km/s/Mpc)")
    h0_error: Optional[float] = Field(None, description="Error on H0 estimate")
    is_valid: bool = Field(False, description="Pixel meets minimum SN count threshold")

    @field_validator('pixel_index')
    @classmethod
    def validate_index_range(cls, v, info):
        """Validate pixel index is within bounds for given Nside."""
        # Nside is available in info.data if populated before validation
        nside = info.data.get('nside')
        if nside is not None:
            max_idx = 12 * (nside ** 2)
            if v < 0 or v >= max_idx:
                raise ValueError(f"Pixel index {v} out of range for Nside={nside}")
        return v

    @field_validator('ra_center')
    @classmethod
    def validate_ra_center(cls, v):
        if v < 0:
            return v + 360.0
        if v >= 360:
            return v % 360.0
        return v

    @field_validator('dec_center')
    @classmethod
    def validate_dec_center(cls, v):
        if v < -90.0:
            return -90.0
        if v > 90.0:
            return 90.0
        return v

    @field_validator('h0_error')
    @classmethod
    def validate_h0_error(cls, v, info):
        """If h0_estimate exists, error must be positive."""
        h0_est = info.data.get('h0_estimate')
        if h0_est is not None and v is not None:
            if v <= 0:
                raise ValueError("H0 error must be positive when H0 estimate exists")
        return v
