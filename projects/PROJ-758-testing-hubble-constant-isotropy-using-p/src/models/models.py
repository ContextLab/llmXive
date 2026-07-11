"""
Pydantic data models for the Hubble Constant Isotropy analysis pipeline.

Defines strict schemas for:
- SupernovaRecord: Raw and processed Pantheon+ supernova data
- HEALPixPixel: Spatial indexing metadata
- H0Estimate: Results from H0 fitting procedures
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
import numpy as np
from datetime import datetime


class SupernovaRecord(BaseModel):
    """
    Represents a single supernova entry from the Pantheon+ dataset.

    Attributes:
        snid: Unique supernova identifier
        ra: Right Ascension in degrees (J2000)
        dec: Declination in degrees (J2000)
        z: Redshift (heliocentric or CMB frame depending on source)
        z_err: Uncertainty in redshift
        distmod: Distance modulus (m - M)
        distmod_err: Uncertainty in distance modulus
        hostmass: Log of host galaxy stellar mass (optional)
        hostmass_err: Uncertainty in host mass (optional)
        ccf: Color correction factor (optional)
        x1: Light curve stretch parameter (optional)
        x1_err: Uncertainty in stretch (optional)
        x0: Amplitude parameter (optional)
        x0_err: Uncertainty in amplitude (optional)
        quality_flag: Quality indicator (0=bad, 1=good)
        healpix_index: Assigned HEALPix pixel index (Nside=4, NESTED)
        source: Origin of the data (e.g., 'pantheon_plus')
        processed_at: Timestamp of data processing
    """
    model_config = ConfigDict(extra="forbid", frozen=False)

    snid: str = Field(..., description="Unique supernova identifier")
    ra: float = Field(..., ge=0.0, le=360.0, description="Right Ascension (degrees)")
    dec: float = Field(..., ge=-90.0, le=90.0, description="Declination (degrees)")
    z: float = Field(..., gt=0.0, description="Redshift")
    z_err: Optional[float] = Field(None, ge=0.0, description="Redshift uncertainty")
    distmod: float = Field(..., description="Distance modulus")
    distmod_err: float = Field(..., ge=0.0, description="Distance modulus uncertainty")
    hostmass: Optional[float] = Field(None, description="Log host mass")
    hostmass_err: Optional[float] = Field(None, ge=0.0, description="Log host mass uncertainty")
    ccf: Optional[float] = Field(None, description="Color correction factor")
    x1: Optional[float] = Field(None, description="Stretch parameter")
    x1_err: Optional[float] = Field(None, ge=0.0, description="Stretch uncertainty")
    x0: Optional[float] = Field(None, description="Amplitude parameter")
    x0_err: Optional[float] = Field(None, ge=0.0, description="Amplitude uncertainty")
    quality_flag: int = Field(1, ge=0, le=1, description="Quality flag (1=good)")
    healpix_index: Optional[int] = Field(None, ge=0, description="HEALPix pixel index")
    source: str = Field("pantheon_plus", description="Data source identifier")
    processed_at: datetime = Field(default_factory=datetime.utcnow, description="Processing timestamp")

    @field_validator('ra')
    @classmethod
    def validate_ra(cls, v):
        if not (0.0 <= v <= 360.0):
            raise ValueError(f"RA must be between 0 and 360, got {v}")
        return v

    @field_validator('dec')
    @classmethod
    def validate_dec(cls, v):
        if not (-90.0 <= v <= 90.0):
            raise ValueError(f"Dec must be between -90 and 90, got {v}")
        return v

    @field_validator('z')
    @classmethod
    def validate_z(cls, v):
        if v <= 0.0:
            raise ValueError(f"Redshift must be positive, got {v}")
        return v


class HEALPixPixel(BaseModel):
    """
    Represents a single HEALPix pixel in the sky partition.

    Attributes:
        pixel_id: The integer index of the pixel
        nside: Resolution parameter (e.g., 4)
        order: Ordering scheme ('NESTED' or 'RING')
        ra_center: Right Ascension of pixel center (degrees)
        dec_center: Declination of pixel center (degrees)
        area_sq_deg: Solid angle of the pixel in square degrees
        n_supernovae: Number of supernovae assigned to this pixel
        supernova_ids: List of SNIDs in this pixel
    """
    model_config = ConfigDict(extra="forbid")

    pixel_id: int = Field(..., ge=0, description="HEALPix pixel index")
    nside: int = Field(..., gt=0, description="HEALPix Nside parameter")
    order: str = Field("NESTED", pattern="^(NESTED|RING)$", description="Pixel ordering scheme")
    ra_center: float = Field(..., ge=0.0, le=360.0, description="Center RA (degrees)")
    dec_center: float = Field(..., ge=-90.0, le=90.0, description="Center Dec (degrees)")
    area_sq_deg: float = Field(..., gt=0.0, description="Pixel area in sq degrees")
    n_supernovae: int = Field(0, ge=0, description="Count of supernovae")
    supernova_ids: List[str] = Field(default_factory=list, description="List of SNIDs")

    @field_validator('pixel_id')
    @classmethod
    def validate_pixel_id(cls, v, info):
        # Basic validation: pixel_id must be < 12 * nside^2
        if 'nside' in info.data:
            nside = info.data['nside']
            max_pixels = 12 * (nside ** 2)
            if v >= max_pixels:
                raise ValueError(f"Pixel ID {v} exceeds max for Nside={nside} ({max_pixels-1})")
        return v


class H0Estimate(BaseModel):
    """
    Represents a single H0 estimate derived from a region or the full sample.

    Attributes:
        estimate_id: Unique identifier for this estimate
        pixel_id: Associated HEALPix pixel (None if global)
        h_value: Estimated H0 value (km/s/Mpc)
        h0_error: Statistical uncertainty (km/s/Mpc)
        method: Fitting method used (e.g., 'linear', 'full_nonlinear', 'hierarchical')
        n_supernovae: Number of supernovae used in fit
        z_min: Minimum redshift of sample
        z_max: Maximum redshift of sample
        chi2: Chi-squared of the fit
        dof: Degrees of freedom
        is_low_n: Boolean flag if N < threshold (e.g., 30)
        hierarchical_corrected: Boolean flag if hierarchical model was applied
        timestamp: Time of estimation
    """
    model_config = ConfigDict(extra="forbid")

    estimate_id: str = Field(..., description="Unique estimate identifier")
    pixel_id: Optional[int] = Field(None, ge=0, description="Associated HEALPix pixel")
    h_value: float = Field(..., gt=0.0, description="H0 value (km/s/Mpc)")
    h0_error: float = Field(..., gt=0.0, description="Uncertainty (km/s/Mpc)")
    method: str = Field(..., description="Fitting method")
    n_supernovae: int = Field(..., ge=1, description="Sample size")
    z_min: float = Field(..., gt=0.0, description="Min redshift")
    z_max: float = Field(..., gt=0.0, description="Max redshift")
    chi2: Optional[float] = Field(None, ge=0.0, description="Chi-squared")
    dof: Optional[int] = Field(None, ge=0, description="Degrees of freedom")
    is_low_n: bool = Field(False, description="Flag for low sample size")
    hierarchical_corrected: bool = Field(False, description="Flag for Bayesian correction")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Estimation time")