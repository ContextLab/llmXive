"""
Data models for the Exoplanetary Atmosphere Characterization pipeline.

Defines core data structures for spectrum metadata and retrieval results,
including support for censored data (upper limits).
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import numpy as np
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PlanetCategory(Enum):
    """Enumeration of exoplanet categories supported by the pipeline."""
    HOT_JUPITER = "Hot Jupiter"
    SUPER_EARTH = "Super Earth"
    NEPTUNE_LIKE = "Neptune-like"
    OTHER = "Other"


class CensorshipStatus(Enum):
    """
    Enumeration for data censorship status.
    Used to distinguish between detected values and upper limits.
    """
    DETECTED = "detected"
    UPPER_LIMIT = "upper_limit"
    MISSING = "missing"


@dataclass
class ExoplanetSpectrum:
    """
    Data model for an exoplanet transmission or emission spectrum.

    Attributes:
        planet_name: Unique identifier for the planet (e.g., 'HD 209458 b').
        host_star_name: Name of the host star.
        planet_category: Category of the exoplanet.
        equilibrium_temp_k: Equilibrium temperature in Kelvin.
        host_metallicity: Host star metallicity [Fe/H].
        spectral_resolution: Spectral resolution (R = lambda / delta_lambda).
        snr: Signal-to-noise ratio of the spectrum.
        wavelengths: Array of wavelength values (microns).
        flux: Array of flux/transit depth values.
        flux_errors: Array of flux uncertainty values.
        censorship_status: Status of the measurement (Detected vs Upper Limit).
        source_file: Path to the raw spectrum file.
        metadata_raw: Dictionary of any additional raw metadata from the source.
    """
    planet_name: str
    host_star_name: str
    planet_category: PlanetCategory
    equilibrium_temp_k: float
    host_metallicity: float
    spectral_resolution: float
    snr: float
    wavelengths: np.ndarray
    flux: np.ndarray
    flux_errors: np.ndarray
    censorship_status: CensorshipStatus = CensorshipStatus.DETECTED
    source_file: Optional[str] = None
    metadata_raw: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate array shapes and types after initialization."""
        if not isinstance(self.wavelengths, np.ndarray):
            self.wavelengths = np.array(self.wavelengths, dtype=float)
        if not isinstance(self.flux, np.ndarray):
            self.flux = np.array(self.flux, dtype=float)
        if not isinstance(self.flux_errors, np.ndarray):
            self.flux_errors = np.array(self.flux_errors, dtype=float)

        if self.wavelengths.shape != self.flux.shape:
            raise ValueError(
                f"Wavelengths and Flux shapes must match: "
                f"{self.wavelengths.shape} vs {self.flux.shape}"
            )
        if self.wavelengths.shape != self.flux_errors.shape:
            raise ValueError(
                f"Wavelengths and Flux errors shapes must match: "
                f"{self.wavelengths.shape} vs {self.flux_errors.shape}"
            )

        # Validate numeric fields
        if self.equilibrium_temp_k <= 0:
            raise ValueError("Equilibrium temperature must be positive.")
        if self.spectral_resolution <= 0:
            raise ValueError("Spectral resolution must be positive.")
        if self.snr <= 0:
            raise ValueError("SNR must be positive.")

    def to_dict(self) -> Dict[str, Any]:
        """Convert the object to a dictionary for serialization."""
        return {
            "planet_name": self.planet_name,
            "host_star_name": self.host_star_name,
            "planet_category": self.planet_category.value,
            "equilibrium_temp_k": self.equilibrium_temp_k,
            "host_metallicity": self.host_metallicity,
            "spectral_resolution": self.spectral_resolution,
            "snr": self.snr,
            "censorship_status": self.censorship_status.value,
            "source_file": self.source_file,
            "wavelengths": self.wavelengths.tolist(),
            "flux": self.flux.tolist(),
            "flux_errors": self.flux_errors.tolist(),
            "metadata_raw": self.metadata_raw
        }


@dataclass
class RetrievalResult:
    """
    Data model for the result of an atmospheric retrieval (petitRADTRANS).

    Represents the derived atmospheric parameters, specifically water abundance,
    handling censored data where the retrieval did not converge or SNR was too low.

    Attributes:
        planet_name: Identifier for the planet.
        water_log_mixing_ratio: Log10 of the water vapor mixing ratio.
        water_log_mixing_ratio_std: 1-sigma uncertainty on the log mixing ratio.
        is_censored: Boolean flag indicating if this is an upper limit.
        upper_limit_value: The value of the upper limit if censored (else None).
        retrieval_converged: Boolean indicating if the retrieval algorithm converged.
        chi_squared: Goodness of fit metric (if available).
        free_parameters: Dictionary of other retrieved parameters (e.g., metallicity, C/O).
        processing_time_s: Time taken for the retrieval in seconds.
    """
    planet_name: str
    water_log_mixing_ratio: Optional[float] = None
    water_log_mixing_ratio_std: Optional[float] = None
    is_censored: bool = False
    upper_limit_value: Optional[float] = None
    retrieval_converged: bool = False
    chi_squared: Optional[float] = None
    free_parameters: Dict[str, float] = field(default_factory=dict)
    processing_time_s: float = 0.0

    def __post_init__(self):
        """Validate internal consistency."""
        if self.is_censored:
            if self.upper_limit_value is None:
                logger.warning(
                    f"Censored result for {self.planet_name} has no upper limit value set."
                )
            # For censored data, the 'value' is the upper limit, std might be undefined or 0
            if self.water_log_mixing_ratio is None:
                self.water_log_mixing_ratio = self.upper_limit_value
        else:
            if self.water_log_mixing_ratio is None:
                raise ValueError(
                    f"Non-censored retrieval result for {self.planet_name} "
                    "must have a water_log_mixing_ratio."
                )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the object to a dictionary for serialization."""
        return {
            "planet_name": self.planet_name,
            "water_log_mixing_ratio": self.water_log_mixing_ratio,
            "water_log_mixing_ratio_std": self.water_log_mixing_ratio_std,
            "is_censored": self.is_censored,
            "upper_limit_value": self.upper_limit_value,
            "retrieval_converged": self.retrieval_converged,
            "chi_squared": self.chi_squared,
            "free_parameters": self.free_parameters,
            "processing_time_s": self.processing_time_s
        }

    @classmethod
    def create_upper_limit(
        cls,
        planet_name: str,
        upper_limit_log_ratio: float,
        reason: str = "Low SNR"
    ) -> 'RetrievalResult':
        """
        Factory method to create a censored retrieval result (upper limit).

        Args:
            planet_name: The planet identifier.
            upper_limit_log_ratio: The calculated upper limit in log10 space.
            reason: Reason for the upper limit (e.g., "Low SNR", "Non-convergence").

        Returns:
            A RetrievalResult instance marked as censored.
        """
        return cls(
            planet_name=planet_name,
            water_log_mixing_ratio=upper_limit_log_ratio,
            water_log_mixing_ratio_std=0.0, # Undefined for upper limits in this context
            is_censored=True,
            upper_limit_value=upper_limit_log_ratio,
            retrieval_converged=False,
            free_parameters={"censor_reason": reason}
        )