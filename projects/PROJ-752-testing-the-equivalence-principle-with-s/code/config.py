"""
Configuration module for the Equivalence Principle Testing Pipeline.

Loads paths, hyperparameters, and verified dataset URLs.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class Config:
    """Pipeline configuration."""
    # Paths
    data_dir: str = field(default_factory=lambda: os.path.join(os.path.dirname(__file__), '..', 'data'))
    code_dir: str = field(default_factory=lambda: os.path.join(os.path.dirname(__file__), '..'))
    
    # Hyperparameters
    residual_threshold_m: float = 0.02
    min_satellite_points: int = 500
    
    # Verified Dataset URLs (Hardcoded as per T009)
    verified_dataset_urls: Dict[str, str] = field(default_factory=lambda: {
        "LAGEOS-1": "https://cddis.nasa.gov/2gpd/data/slr/normal_points/lageos1",
        "LAGEOS-2": "https://cddis.nasa.gov/2gpd/data/slr/normal_points/lageos2",
        "Etalon-1": "https://cddis.nasa.gov/2gpd/data/slr/normal_points/etalon1",
        "Etalon-2": "https://cddis.nasa.gov/2gpd/data/slr/normal_points/etalon2",
        "Starlette": "https://cddis.nasa.gov/2gpd/data/slr/normal_points/starlette"
    })

def get_config() -> Config:
    """
    Get the global configuration instance.

    Returns:
        Config object.
    """
    return Config()
