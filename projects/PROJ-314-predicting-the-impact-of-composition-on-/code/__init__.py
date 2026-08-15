import logging
import os
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import hashlib

# Ensure logs directory exists
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Configure project logger
def get_logger(name: str = "llmXive") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        # File handler for persistent logs
        log_file = LOGS_DIR / "pipeline.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # Console handler for immediate feedback
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        logger.setLevel(logging.DEBUG)
    return logger

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "pipeline.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("llmXive")

# Import config
from .config import load_environment, initialize_config

# Initialize config on import
initialize_config()

@dataclass
class CeramicEntry:
    """
    Dataclass representing a single ceramic material entry.
    Corresponds to the raw or processed row in the dataset.
    
    Attributes:
        composition: Chemical formula string (e.g., "Al2O3").
        weibull_modulus: The Weibull modulus value (target variable).
        mean_strength: Mean flexural strength in MPa.
        standard_deviation: Standard deviation of strength measurements.
        sintering_temp: Sintering temperature in Celsius.
        sintering_time: Sintering time in hours.
        source_id: Identifier for the source publication/dataset.
        raw_data: Dictionary containing all original fields from the source.
    """
    composition: str
    weibull_modulus: Optional[float] = None
    mean_strength: Optional[float] = None
    standard_deviation: Optional[float] = None
    sintering_temp: Optional[float] = None
    sintering_time: Optional[float] = None
    source_id: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the CeramicEntry to a dictionary representation."""
        return {
            "composition": self.composition,
            "weibull_modulus": self.weibull_modulus,
            "mean_strength": self.mean_strength,
            "standard_deviation": self.standard_deviation,
            "sintering_temp": self.sintering_temp,
            "sintering_time": self.sintering_time,
            "source_id": self.source_id,
            "raw_data": self.raw_data
        }

@dataclass
class DescriptorSet:
    """
    Represents a set of computed elemental descriptors for a ceramic composition.
    
    This class encapsulates the feature vector derived from a chemical formula,
    including physical and chemical properties used for predictive modeling.
    
    Attributes:
        composition (str): The original chemical formula string (e.g., "Al2O3").
        mean_atomic_radius (float): Mean atomic radius of constituent elements.
        electronegativity_std (float): Standard deviation of electronegativity.
        valence_electron_concentration (float): Valence electron concentration (VEC).
        cation_size_variance (float): Variance of cation atomic radii.
        range_uncertainty (float): Uncertainty metric derived from range values.
        primary_anion_cation_group (str): Identified primary anion-cation group (e.g., "O-Al").
        is_range_flag (bool): Flag indicating if original values were ranges.
        is_imputed (bool): Flag indicating if any values were imputed.
        sample_count (int): Number of samples for this entry.
        weibull_modulus (float): The target Weibull modulus value.
        sintering_temp (float): Sintering temperature in Kelvin.
        raw_data (dict): Dictionary containing raw descriptor values before aggregation.
    """
    composition: str
    mean_atomic_radius: Optional[float] = None
    electronegativity_std: Optional[float] = None
    valence_electron_concentration: Optional[float] = None
    cation_size_variance: Optional[float] = None
    range_uncertainty: Optional[float] = None
    primary_anion_cation_group: Optional[str] = None
    is_range_flag: bool = False
    is_imputed: bool = False
    sample_count: int = 0
    weibull_modulus: Optional[float] = None
    sintering_temp: Optional[float] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the DescriptorSet to a dictionary representation."""
        return {
            "composition": self.composition,
            "mean_atomic_radius": self.mean_atomic_radius,
            "electronegativity_std": self.electronegativity_std,
            "valence_electron_concentration": self.valence_electron_concentration,
            "cation_size_variance": self.cation_size_variance,
            "range_uncertainty": self.range_uncertainty,
            "primary_anion_cation_group": self.primary_anion_cation_group,
            "is_range_flag": self.is_range_flag,
            "is_imputed": self.is_imputed,
            "sample_count": self.sample_count,
            "weibull_modulus": self.weibull_modulus,
            "sintering_temp": self.sintering_temp,
            "raw_data": self.raw_data
        }
    
    def __post_init__(self):
        """Validate that composition is not empty."""
        if not self.composition or not self.composition.strip():
            raise ValueError("Composition string cannot be empty.")

def hash_string(s: str) -> str:
    """Helper to hash strings for versioning."""
    return hashlib.sha256(s.encode('utf-8')).hexdigest()[:12]
