"""
llmXive Research Pipeline - Code Package
PROJ-314: Predicting the Impact of Composition on the Weibull Modulus of Ceramics
"""
import logging
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import hashlib

# Configure project logger
def get_logger(name: str = "llmXive") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

logger = get_logger()

__version__ = "0.1.0"

@dataclass
class CeramicEntry:
    """
    Dataclass representing a single ceramic material entry.
    Corresponds to the raw or processed row in the dataset.
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
    Dataclass representing computed elemental descriptors for a composition.
    Used to store the feature vector derived from a CeramicEntry.
    
    Attributes:
        composition: The chemical formula string (e.g., "Al2O3").
        mean_atomic_radius: Weighted mean atomic radius of constituent elements.
        electronegativity_std: Standard deviation of electronegativity values.
        valence_electron_concentration: Average valence electrons per atom (VEC).
        cation_size_variance: Variance in ionic radii of cations.
        primary_anion_cation_group: Dominant chemical group classification (e.g., "Oxide").
        is_imputed: Flag indicating if any values were imputed.
        imputation_details: Dictionary detailing which fields were imputed and the method used.
    """
    composition: str
    mean_atomic_radius: Optional[float] = None
    electronegativity_std: Optional[float] = None
    valence_electron_concentration: Optional[float] = None
    cation_size_variance: Optional[float] = None
    primary_anion_cation_group: Optional[str] = None
    is_imputed: bool = False
    imputation_details: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "composition": self.composition,
            "mean_atomic_radius": self.mean_atomic_radius,
            "electronegativity_std": self.electronegativity_std,
            "valence_electron_concentration": self.valence_electron_concentration,
            "cation_size_variance": self.cation_size_variance,
            "primary_anion_cation_group": self.primary_anion_cation_group,
            "is_imputed": self.is_imputed,
            "imputation_details": self.imputation_details
        }

def hash_string(s: str) -> str:
    """Helper to hash strings for versioning."""
    return hashlib.sha256(s.encode('utf-8')).hexdigest()[:12]