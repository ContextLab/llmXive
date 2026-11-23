"""
Pydantic model for Pantheon+ Supernova records.

Defines the schema for individual supernova observations including
celestial coordinates, redshift, and magnitude data.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import math

class SupernovaRecord(BaseModel):
    """
    Represents a single supernova observation from the Pantheon+ sample.

    Attributes:
        supernova_id: Unique identifier for the supernova (e.g., 'SN2012fr')
        ra: Right Ascension in degrees (0 to 360)
        dec: Declination in degrees (-90 to 90)
        z: Redshift (dimensionless)
        z_hel: Heliocentric redshift
        z_cmb: CMB frame redshift
        dm: Distance modulus (magnitudes)
        dm_err: Uncertainty in distance modulus
        host_mass: Host galaxy stellar mass (log M_sun), optional
        host_mass_err: Uncertainty in host mass, optional
        quality_flag: Data quality indicator (0=good, 1=warning, 2=bad)
        survey: Survey name (e.g., 'SDSS', 'SNLS', 'PanSTARRS')
        healpix_index: Assigned HEALPix pixel index (NESTED scheme)
    """
    supernova_id: str = Field(..., description="Unique supernova identifier")
    ra: float = Field(..., ge=0.0, le=360.0, description="Right Ascension (degrees)")
    dec: float = Field(..., ge=-90.0, le=90.0, description="Declination (degrees)")
    z: float = Field(..., gt=0.0, description="Redshift")
    z_hel: float = Field(..., description="Heliocentric redshift")
    z_cmb: float = Field(..., description="CMB frame redshift")
    dm: float = Field(..., description="Distance modulus")
    dm_err: float = Field(..., gt=0.0, description="Distance modulus error")
    host_mass: Optional[float] = Field(None, description="Host galaxy log mass")
    host_mass_err: Optional[float] = Field(None, description="Host mass error")
    quality_flag: int = Field(0, ge=0, le=2, description="Quality flag")
    survey: str = Field(..., description="Survey name")
    healpix_index: Optional[int] = Field(None, description="HEALPix NESTED index")

    @field_validator('ra')
    @classmethod
    def validate_ra(cls, v):
        """Ensure RA is normalized to [0, 360)."""
        if v < 0:
            return v + 360.0
        if v >= 360:
            return v % 360.0
        return v

    @field_validator('dec')
    @classmethod
    def validate_dec(cls, v):
        """Ensure Dec is within valid bounds."""
        if v < -90.0:
            return -90.0
        if v > 90.0:
            return 90.0
        return v

    @field_validator('z')
    @classmethod
    def validate_z(cls, v):
        """Ensure redshift is positive."""
        if v <= 0:
            raise ValueError("Redshift must be positive")
        return v

    @field_validator('dm_err')
    @classmethod
    def validate_dm_err(cls, v):
        """Ensure distance modulus error is positive."""
        if v <= 0:
            raise ValueError("Distance modulus error must be positive")
        return v
