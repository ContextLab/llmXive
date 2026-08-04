"""
Data models for exoplanetary atmosphere characterization pipeline.

Defines core data structures for spectrum metadata and retrieval results,
including support for censored data (upper limits) as required by the
statistical analysis of low S/N observations.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import numpy as np
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PlanetCategory(Enum):
    """Classification of exoplanet types based on mass and radius."""
    HOT_JUPITER = "Hot Jupiter"
    SUPER_EARTH = "Super Earth"
    NEPTUNE_LIKE = "Neptune-like"
    UNKNOWN = "Unknown"

    @classmethod
    def from_string(cls, value: Optional[str]) -> "PlanetCategory":
        """Convert string to enum, defaulting to UNKNOWN if invalid."""
        if not value:
            return cls.UNKNOWN
        value = value.strip().upper()
        if "HOT JUPITER" in value or "HJ" in value:
            return cls.HOT_JUPITER
        if "SUPER EARTH" in value or "SE" in value:
            return cls.SUPER_EARTH
        if "NEPTUNE" in value or "NL" in value:
            return cls.NEPTUNE_LIKE
        return cls.UNKNOWN


class CensorshipStatus(Enum):
    """Status of data points regarding censorship (upper limits)."""
    DETECTED = "detected"
    UPPER_LIMIT = "upper_limit"
    UNKNOWN = "unknown"

    @classmethod
    def from_snr(cls, snr: Optional[float], threshold: float = 3.0) -> "CensorshipStatus":
        """
        Determine censorship status based on Signal-to-Noise Ratio.

        Args:
            snr: Signal-to-noise ratio value.
            threshold: SNR threshold below which data is considered censored.

        Returns:
            CensorshipStatus enum value.
        """
        if snr is None:
            return cls.UNKNOWN
        if snr < threshold:
            return cls.UPPER_LIMIT
        return cls.DETECTED


@dataclass
class ExoplanetSpectrum:
    """
    Represents a transmission spectrum and its associated metadata.

    Attributes:
        planet_name: Unique identifier for the exoplanet.
        host_star_name: Name of the host star.
        equilibrium_temp_k: Equilibrium temperature in Kelvin.
        host_metallicity: Host star metallicity [Fe/H].
        spectral_resolution: Spectral resolution (R = lambda/delta_lambda).
        snr: Signal-to-noise ratio of the spectrum.
        category: Planet category (Hot Jupiter, Super Earth, etc.).
        wavelength_microns: Array of wavelength values in microns.
        flux_values: Array of transit depth or flux values.
        flux_uncertainties: Array of uncertainties for flux values.
        censorship_status: Status indicating if data is censored (upper limit).
        raw_file_path: Path to the raw spectrum file.
        metadata_source: Source of the metadata (e.g., 'NASA Exoplanet Archive').
        retrieval_status: Status of retrieval processing (e.g., 'pending', 'completed').
    """
    planet_name: str
    host_star_name: str
    equilibrium_temp_k: Optional[float] = None
    host_metallicity: Optional[float] = None
    spectral_resolution: Optional[float] = None
    snr: Optional[float] = None
    category: PlanetCategory = PlanetCategory.UNKNOWN
    wavelength_microns: Optional[np.ndarray] = field(default=None)
    flux_values: Optional[np.ndarray] = field(default=None)
    flux_uncertainties: Optional[np.ndarray] = field(default=None)
    censorship_status: CensorshipStatus = CensorshipStatus.UNKNOWN
    raw_file_path: Optional[str] = None
    metadata_source: str = "NASA Exoplanet Archive"
    retrieval_status: str = "pending"

    def __post_init__(self):
        """Validate and initialize derived fields."""
        # Determine censorship status if SNR is available
        if self.snr is not None and self.censorship_status == CensorshipStatus.UNKNOWN:
            self.censorship_status = CensorshipStatus.from_snr(self.snr)

        # Validate arrays if provided
        if self.wavelength_microns is not None:
            self.wavelength_microns = np.asarray(self.wavelength_microns)
        if self.flux_values is not None:
            self.flux_values = np.asarray(self.flux_values)
        if self.flux_uncertainties is not None:
            self.flux_uncertainties = np.asarray(self.flux_uncertainties)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "planet_name": self.planet_name,
            "host_star_name": self.host_star_name,
            "equilibrium_temp_k": self.equilibrium_temp_k,
            "host_metallicity": self.host_metallicity,
            "spectral_resolution": self.spectral_resolution,
            "snr": self.snr,
            "category": self.category.value,
            "censorship_status": self.censorship_status.value,
            "raw_file_path": self.raw_file_path,
            "metadata_source": self.metadata_source,
            "retrieval_status": self.retrieval_status,
            "wavelength_microns": self.wavelength_microns.tolist() if self.wavelength_microns is not None else None,
            "flux_values": self.flux_values.tolist() if self.flux_values is not None else None,
            "flux_uncertainties": self.flux_uncertainties.tolist() if self.flux_uncertainties is not None else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExoplanetSpectrum":
        """Create instance from dictionary."""
        # Handle enum conversion
        if "category" in data and isinstance(data["category"], str):
            data["category"] = PlanetCategory.from_string(data["category"])
        if "censorship_status" in data and isinstance(data["censorship_status"], str):
            try:
                data["censorship_status"] = CensorshipStatus(data["censorship_status"])
            except ValueError:
                data["censorship_status"] = CensorshipStatus.UNKNOWN

        # Handle numpy array conversion
        if "wavelength_microns" in data and data["wavelength_microns"] is not None:
            data["wavelength_microns"] = np.array(data["wavelength_microns"])
        if "flux_values" in data and data["flux_values"] is not None:
            data["flux_values"] = np.array(data["flux_values"])
        if "flux_uncertainties" in data and data["flux_uncertainties"] is not None:
            data["flux_uncertainties"] = np.array(data["flux_uncertainties"])

        return cls(**data)


@dataclass
class RetrievalResult:
    """
    Represents the output of an atmospheric retrieval run using petitRADTRANS.

    Attributes:
        planet_name: Unique identifier for the exoplanet.
        water_log_mixing_ratio: Log10 of the water vapor mixing ratio.
        water_std: Standard deviation of the water mixing ratio (uncertainty).
        water_upper_limit: Boolean flag indicating if value is an upper limit.
        temperature_log_mixing_ratio: Log10 of the temperature mixing ratio (if applicable).
        temperature_std: Standard deviation for temperature mixing ratio.
        temperature_upper_limit: Boolean flag for temperature upper limit.
        other_species: Dictionary of other species mixing ratios and uncertainties.
        retrieval_converged: Boolean indicating if retrieval converged.
        retrieval_iterations: Number of iterations performed.
        log_likelihood: Final log-likelihood value.
        snr_at_input: Signal-to-noise ratio of the input spectrum.
        spectral_resolution_at_input: Spectral resolution of the input spectrum.
        censorship_status: Censorship status derived from input SNR.
        processing_time_seconds: Time taken for retrieval.
        error_message: Error message if retrieval failed.
    """
    planet_name: str
    water_log_mixing_ratio: Optional[float] = None
    water_std: Optional[float] = None
    water_upper_limit: bool = False
    temperature_log_mixing_ratio: Optional[float] = None
    temperature_std: Optional[float] = None
    temperature_upper_limit: bool = False
    other_species: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    retrieval_converged: bool = True
    retrieval_iterations: int = 0
    log_likelihood: Optional[float] = None
    snr_at_input: Optional[float] = None
    spectral_resolution_at_input: Optional[float] = None
    censorship_status: CensorshipStatus = CensorshipStatus.UNKNOWN
    processing_time_seconds: Optional[float] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        """Initialize derived fields and validate data."""
        # If SNR is provided, determine censorship status
        if self.snr_at_input is not None and self.censorship_status == CensorshipStatus.UNKNOWN:
            self.censorship_status = CensorshipStatus.from_snr(self.snr_at_input)

        # If not converged and no error message, set a default one
        if not self.retrieval_converged and not self.error_message:
            self.error_message = "Retrieval did not converge within iteration limit."

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "planet_name": self.planet_name,
            "water_log_mixing_ratio": self.water_log_mixing_ratio,
            "water_std": self.water_std,
            "water_upper_limit": self.water_upper_limit,
            "temperature_log_mixing_ratio": self.temperature_log_mixing_ratio,
            "temperature_std": self.temperature_std,
            "temperature_upper_limit": self.temperature_upper_limit,
            "other_species": self.other_species,
            "retrieval_converged": self.retrieval_converged,
            "retrieval_iterations": self.retrieval_iterations,
            "log_likelihood": self.log_likelihood,
            "snr_at_input": self.snr_at_input,
            "spectral_resolution_at_input": self.spectral_resolution_at_input,
            "censorship_status": self.censorship_status.value,
            "processing_time_seconds": self.processing_time_seconds,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RetrievalResult":
        """Create instance from dictionary."""
        # Handle enum conversion
        if "censorship_status" in data and isinstance(data["censorship_status"], str):
            try:
                data["censorship_status"] = CensorshipStatus(data["censorship_status"])
            except ValueError:
                data["censorship_status"] = CensorshipStatus.UNKNOWN

        return cls(**data)

    def is_upper_limit(self) -> bool:
        """Check if the water abundance is an upper limit."""
        return self.water_upper_limit or self.censorship_status == CensorshipStatus.UPPER_LIMIT

    def get_water_value(self) -> Optional[float]:
        """
        Get the water mixing ratio value.

        For upper limits, returns the negative of the upper limit value
        to distinguish from detected values in statistical analysis.
        """
        if self.water_log_mixing_ratio is None:
            return None
        if self.is_upper_limit():
            # Convention: negative value indicates upper limit
            return -abs(self.water_log_mixing_ratio)
        return self.water_log_mixing_ratio