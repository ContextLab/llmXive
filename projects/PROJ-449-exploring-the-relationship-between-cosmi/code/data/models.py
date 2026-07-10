"""
Data models for cosmic ray flux, solar activity, and composition ratios.

Constitution Principle VI: Rigidity-Dependent Flux Calibration
FR-001: Rigidity Bin Requirement
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import date
import logging

# Configure logger for validation errors
logger = logging.getLogger(__name__)

@dataclass
class CosmicRayFlux:
    """
    Represents a cosmic ray flux measurement.
    
    Constitution Principle VI: Rigidity-Dependent Flux Calibration
    Every flux measurement MUST be tied to a specific rigidity bin.
    
    Attributes:
        date: Observation date
        species: Particle species ('proton', 'helium', 'CNO', 'Fe')
        rigidity: Magnetic rigidity in GV (Gigavolts). Must be > 0.
        flux: Differential flux in (m^2 s sr GeV)^-1
        flux_error: Optional measurement uncertainty
        source: Data source identifier (default: "AMS-02")
    
    Raises:
        ValueError: If rigidity is missing, non-positive, or flux is invalid.
    """
    date: date
    species: str
    rigidity: float
    flux: float
    flux_error: Optional[float] = None
    source: str = "AMS-02"

    def __post_init__(self):
        """Validate that rigidity is present and positive (Constitution Principle VI)."""
        if self.rigidity is None:
            raise ValueError("CosmicRayFlux: rigidity attribute is required (Constitution Principle VI).")
        if not isinstance(self.rigidity, (int, float)):
            raise ValueError(f"CosmicRayFlux: rigidity must be a number, got {type(self.rigidity)}")
        if self.rigidity <= 0:
            raise ValueError(f"CosmicRayFlux: rigidity must be positive, got {self.rigidity} GV.")
        
        if self.flux is None:
            raise ValueError("CosmicRayFlux: flux value is required.")
        
        if self.species.lower() not in ['proton', 'helium', 'cno', 'fe']:
            logger.warning(f"CosmicRayFlux: Unrecognized species '{self.species}'. Expected 'proton', 'helium', 'CNO', or 'Fe'.")

@dataclass
class SolarActivityIndex:
    """
    Represents a solar activity measurement (e.g., sunspot number).
    
    Attributes:
        date: Observation date
        index_type: Type of index (e.g., 'sunspot_number', 'solar_flux')
        value: Measured value
        source: Data source identifier (default: "NOAA")
    """
    date: date
    index_type: str
    value: float
    source: str = "NOAA"

    def __post_init__(self):
        """Validate basic constraints."""
        if self.value is None:
            raise ValueError("SolarActivityIndex: value is required.")
        if self.index_type.lower() not in ['sunspot_number', 'solar_flux', 'cosmic_ray_forbush_decrease']:
            logger.warning(f"SolarActivityIndex: Unrecognized index_type '{self.index_type}'.")

@dataclass
class CompositionRatio:
    """
    Represents a calculated composition ratio (e.g., He/p, Fe/p).
    
    FR-003: Denominator Handling
    If proton flux is zero or missing, ratio is undefined.
    
    Attributes:
        date: Observation date
        numerator_species: Species in numerator ('helium', 'Fe', 'CNO')
        denominator_species: Species in denominator ('proton')
        rigidity: Rigidity bin for the ratio (GV)
        ratio_value: Calculated ratio value (optional if below detection)
        ratio_error: Uncertainty in the ratio
        is_below_detection_limit: True if denominator was zero/missing
        source: Calculation source
    """
    date: date
    numerator_species: str
    denominator_species: str
    rigidity: float
    ratio_value: Optional[float] = None
    ratio_error: Optional[float] = None
    is_below_detection_limit: bool = False
    source: str = "Calculated"

    def __post_init__(self):
        """Validate ratio constraints."""
        if self.rigidity is None or self.rigidity <= 0:
            raise ValueError("CompositionRatio: rigidity must be a positive number.")
        
        if not self.is_below_detection_limit and self.ratio_value is None:
            raise ValueError("CompositionRatio: ratio_value is required unless is_below_detection_limit is True.")
        
        if self.denominator_species.lower() != 'proton':
            logger.warning(f"CompositionRatio: Standard denominator is 'proton', got '{self.denominator_species}'.")
        
        if self.numerator_species.lower() not in ['helium', 'fe', 'cno']:
            logger.warning(f"CompositionRatio: Unrecognized numerator_species '{self.numerator_species}'.")