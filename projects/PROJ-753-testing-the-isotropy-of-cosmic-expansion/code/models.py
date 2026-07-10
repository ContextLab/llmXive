"""
Base data models for the isotropy analysis pipeline.

This module defines the core dataclasses used to represent supernova records,
HEALPix pixel assignments, and harmonic decomposition coefficients.
"""

from dataclasses import dataclass, field
from typing import Optional
import math


@dataclass(frozen=True)
class SupernovaRecord:
    """
    Represents a single Type Ia Supernova entry from the Pantheon+ dataset.

    Attributes:
        id: Unique identifier for the supernova (e.g., 'SN2005cf').
        ra: Right Ascension in degrees (J2000).
        dec: Declination in degrees (J2000).
        z: Redshift.
        mu_obs: Observed distance modulus.
        sigma_mu: Uncertainty in the observed distance modulus.
        mu_th: Theoretical distance modulus calculated from the flat LambdaCDM model.
        residual: The difference mu_obs - mu_th.
    """
    id: str
    ra: float
    dec: float
    z: float
    mu_obs: float
    sigma_mu: float
    mu_th: Optional[float] = None
    residual: Optional[float] = None

    def __post_init__(self) -> None:
        """Validate physical constraints and compute residual if theoretical modulus exists."""
        # Basic validation
        if not (-180.0 <= self.ra <= 180.0):
            raise ValueError(f"RA must be between -180 and 180, got {self.ra}")
        if not (-90.0 <= self.dec <= 90.0):
            raise ValueError(f"Dec must be between -90 and 90, got {self.dec}")
        if self.z < 0:
            raise ValueError(f"Redshift must be non-negative, got {self.z}")
        if self.sigma_mu <= 0:
            raise ValueError(f"Sigma_mu must be positive, got {self.sigma_mu}")

        # Compute residual if theoretical modulus is provided
        if self.mu_th is not None:
            object.__setattr__(self, 'residual', self.mu_obs - self.mu_th)


@dataclass(frozen=True)
class HealpixPixel:
    """
    Represents a pixel in the HEALPix grid.

    Attributes:
        nside: The HEALPix resolution parameter.
        pixel_index: The integer index of the pixel (0 <= pixel_index < 12 * nside^2).
        ra_center: Right Ascension of the pixel center in degrees.
        dec_center: Declination of the pixel center in degrees.
        count: Number of supernovae mapped to this pixel.
        mean_residual: Mean residual of supernovae in this pixel.
        mean_sigma: Mean uncertainty of supernovae in this pixel.
    """
    nside: int
    pixel_index: int
    ra_center: float
    dec_center: float
    count: int = 0
    mean_residual: Optional[float] = None
    mean_sigma: Optional[float] = None

    def __post_init__(self) -> None:
        """Validate HEALPix constraints."""
        if self.nside <= 0:
            raise ValueError(f"Nside must be positive, got {self.nside}")
        max_index = 12 * (self.nside ** 2)
        if not (0 <= self.pixel_index < max_index):
            raise ValueError(f"Pixel index {self.pixel_index} out of range for nside={self.nside}")

    def update_stats(self, residual: float, sigma: float) -> None:
        """
        Update running statistics for this pixel.
        Note: Since this is a frozen dataclass, this method returns a new instance.
        """
        new_count = self.count + 1
        # Update mean incrementally
        if self.mean_residual is None:
            new_mean_res = residual
            new_mean_sig = sigma
        else:
            new_mean_res = self.mean_residual + (residual - self.mean_residual) / new_count
            new_mean_sig = self.mean_sigma + (sigma - self.mean_sigma) / new_count

        return HealpixPixel(
            nside=self.nside,
            pixel_index=self.pixel_index,
            ra_center=self.ra_center,
            dec_center=self.dec_center,
            count=new_count,
            mean_residual=new_mean_res,
            mean_sigma=new_mean_sig
        )


@dataclass(frozen=True)
class HarmonicCoefficient:
    """
    Represents a spherical harmonic coefficient (a_lm) or power spectrum value.

    Attributes:
        l: Multipole moment (angular scale).
        m: Azimuthal order (-l <= m <= l).
        real_part: Real component of the coefficient.
        imag_part: Imaginary component of the coefficient.
        amplitude: Magnitude sqrt(real^2 + imag^2).
        phase: Phase angle atan2(imag, real) in radians.
    """
    l: int
    m: int
    real_part: float
    imag_part: float

    def __post_init__(self) -> None:
        """Validate multipole constraints."""
        if self.l < 0:
            raise ValueError(f"l must be non-negative, got {self.l}")
        if not (-self.l <= self.m <= self.l):
            raise ValueError(f"m must be between -l and l, got {self.m} for l={self.l}")

    @property
    def amplitude(self) -> float:
        """Calculate the amplitude of the harmonic coefficient."""
        return math.sqrt(self.real_part**2 + self.imag_part**2)

    @property
    def phase(self) -> float:
        """Calculate the phase angle of the harmonic coefficient."""
        return math.atan2(self.imag_part, self.real_part)

    @property
    def power(self) -> float:
        """Calculate the power (squared amplitude)."""
        return self.real_part**2 + self.imag_part**2