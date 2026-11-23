from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import numpy as np
from enum import Enum
import logging

class PlanetCategory(Enum):
    HOT_JUPITER = "Hot Jupiter"
    TEMPERATE_SUPER_EARTH = "Temperate Super-Earth"
    OTHER = "Other"
    UNKNOWN = "Unknown"

class CensorshipStatus(Enum):
    DETECTED = "detected"
    UPPER_LIMIT = "upper_limit"
    UNCENSORED = "uncensored"

@dataclass
class ExoplanetSpectrum:
    planet_name: str
    temperature: float
    metallicity: Optional[float]
    snr: float
    resolution: float
    planet_category: PlanetCategory
    instrument: str
    wavelength_range: str
    spectrum_data: Optional[np.ndarray] = None
    
@dataclass
class RetrievalResult:
    planet_name: str
    water_mixing_ratio: float
    uncertainty: float
    is_upper_limit: bool
    detection_limit: float
    min_detectable_concentration: float
    convergence_status: str
    error_message: Optional[str] = None
    
def main():
    """Main entry point for data models module."""
    logging.info("Data models module loaded")

if __name__ == "__main__":
    main()
