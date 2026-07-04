"""
Data models for the Exoplanetary Atmosphere Characterization pipeline.

Defines core data structures for:
- ExoplanetSpectrum: Raw and processed spectral data with metadata.
- RetrievalResult: Results from atmospheric retrieval (water abundance, uncertainties).
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import numpy as np
from enum import Enum

class PlanetCategory(Enum):
    """Classification of exoplanet types based on mass and radius."""
    HOT_JUPITER = "hot_jupiter"
    SUPER_EARTH = "super_earth"
    NEPTUNE = "neptune"
    OTHER = "other"

class CensorshipStatus(Enum):
    """Status of a value regarding censoring (upper limits)."""
    OBSERVED = "observed"
    UPPER_LIMIT = "upper_limit"
    LOWER_LIMIT = "lower_limit"
    UNKNOWN = "unknown"

@dataclass
class ExoplanetSpectrum:
    """
    Represents an exoplanet transmission or emission spectrum with metadata.

    Attributes:
        planet_name: Unique identifier for the planet (e.g., 'HD 209458 b').
        host_star_name: Name of the host star.
        equilibrium_temp_k: Equilibrium temperature in Kelvin.
        host_metallicity: Host star metallicity [Fe/H].
        spectral_resolution: Spectral resolution (R = lambda / delta_lambda).
        snr: Signal-to-noise ratio of the spectrum.
        wavelength_um: Array of wavelengths in micrometers.
        flux: Array of flux values (transit depth or emission).
        flux_error: Array of flux uncertainties.
        category: Planet category (Hot Jupiter, Super-Earth, etc.).
        observation_id: Unique identifier for the observation.
        instrument: Instrument used (e.g., 'HST/WFC3', 'JWST/NIRSpec').
        raw_file_path: Path to the raw spectrum file on disk.
        processed_file_path: Path to the processed spectrum file (if applicable).
    """
    planet_name: str
    host_star_name: str
    equilibrium_temp_k: float
    host_metallicity: float
    spectral_resolution: float
    snr: float
    wavelength_um: np.ndarray
    flux: np.ndarray
    flux_error: np.ndarray
    category: PlanetCategory
    observation_id: str
    instrument: str
    raw_file_path: Optional[str] = None
    processed_file_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure numpy arrays are properly typed."""
        if not isinstance(self.wavelength_um, np.ndarray):
            self.wavelength_um = np.array(self.wavelength_um, dtype=float)
        if not isinstance(self.flux, np.ndarray):
            self.flux = np.array(self.flux, dtype=float)
        if not isinstance(self.flux_error, np.ndarray):
            self.flux_error = np.array(self.flux_error, dtype=float)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the object to a dictionary for serialization."""
        return {
            'planet_name': self.planet_name,
            'host_star_name': self.host_star_name,
            'equilibrium_temp_k': self.equilibrium_temp_k,
            'host_metallicity': self.host_metallicity,
            'spectral_resolution': self.spectral_resolution,
            'snr': self.snr,
            'wavelength_um': self.wavelength_um.tolist(),
            'flux': self.flux.tolist(),
            'flux_error': self.flux_error.tolist(),
            'category': self.category.value,
            'observation_id': self.observation_id,
            'instrument': self.instrument,
            'raw_file_path': self.raw_file_path,
            'processed_file_path': self.processed_file_path,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExoplanetSpectrum':
        """Reconstruct an ExoplanetSpectrum from a dictionary."""
        return cls(
            planet_name=data['planet_name'],
            host_star_name=data['host_star_name'],
            equilibrium_temp_k=data['equilibrium_temp_k'],
            host_metallicity=data['host_metallicity'],
            spectral_resolution=data['spectral_resolution'],
            snr=data['snr'],
            wavelength_um=np.array(data['wavelength_um']),
            flux=np.array(data['flux']),
            flux_error=np.array(data['flux_error']),
            category=PlanetCategory(data['category']),
            observation_id=data['observation_id'],
            instrument=data['instrument'],
            raw_file_path=data.get('raw_file_path'),
            processed_file_path=data.get('processed_file_path'),
            metadata=data.get('metadata', {})
        )

@dataclass
class RetrievalResult:
    """
    Represents the result of an atmospheric retrieval (e.g., water abundance).

    Attributes:
        planet_name: Planet identifier.
        observation_id: Observation identifier.
        log10_h2o_mixing_ratio: Log10 of the water vapor mixing ratio.
        h2o_mixing_ratio_std: Standard deviation (uncertainty) of the mixing ratio.
        is_upper_limit: Boolean flag indicating if the value is an upper limit (censored).
        retrieval_converged: Boolean flag indicating if the retrieval converged.
        model_parameters: Dictionary of other retrieved parameters (e.g., temperature, metallicity).
        log_likelihood: Log-likelihood of the best-fit model.
        posterior_samples: Optional array of posterior samples for the water mixing ratio.
        retrieval_method: Name of the retrieval method used (e.g., 'petitRADTRANS').
        snr_at_retrieval: SNR used during retrieval (for reference).
        resolution_at_retrieval: Resolution used during retrieval (for reference).
    """
    planet_name: str
    observation_id: str
    log10_h2o_mixing_ratio: float
    h2o_mixing_ratio_std: float
    is_upper_limit: bool
    retrieval_converged: bool
    model_parameters: Dict[str, float] = field(default_factory=dict)
    log_likelihood: Optional[float] = None
    posterior_samples: Optional[np.ndarray] = None
    retrieval_method: str = "petitRADTRANS"
    snr_at_retrieval: Optional[float] = None
    resolution_at_retrieval: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the object to a dictionary for serialization."""
        result = {
            'planet_name': self.planet_name,
            'observation_id': self.observation_id,
            'log10_h2o_mixing_ratio': self.log10_h2o_mixing_ratio,
            'h2o_mixing_ratio_std': self.h2o_mixing_ratio_std,
            'is_upper_limit': self.is_upper_limit,
            'retrieval_converged': self.retrieval_converged,
            'model_parameters': self.model_parameters,
            'log_likelihood': self.log_likelihood,
            'retrieval_method': self.retrieval_method,
            'snr_at_retrieval': self.snr_at_retrieval,
            'resolution_at_retrieval': self.resolution_at_retrieval
        }
        if self.posterior_samples is not None:
            result['posterior_samples'] = self.posterior_samples.tolist()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RetrievalResult':
        """Reconstruct a RetrievalResult from a dictionary."""
        posterior = data.get('posterior_samples')
        if posterior is not None:
            posterior = np.array(posterior)
        return cls(
            planet_name=data['planet_name'],
            observation_id=data['observation_id'],
            log10_h2o_mixing_ratio=data['log10_h2o_mixing_ratio'],
            h2o_mixing_ratio_std=data['h2o_mixing_ratio_std'],
            is_upper_limit=data['is_upper_limit'],
            retrieval_converged=data['retrieval_converged'],
            model_parameters=data.get('model_parameters', {}),
            log_likelihood=data.get('log_likelihood'),
            posterior_samples=posterior,
            retrieval_method=data.get('retrieval_method', 'petitRADTRANS'),
            snr_at_retrieval=data.get('snr_at_retrieval'),
            resolution_at_retrieval=data.get('resolution_at_retrieval')
        )

    def get_h2o_mixing_ratio(self) -> float:
        """
        Returns the water mixing ratio in linear scale.
        If it is an upper limit, returns the limit value.
        """
        return 10.0 ** self.log10_h2o_mixing_ratio