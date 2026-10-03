"""
Configuration management for the atmospheric pressure and earthquake correlation study.
Handles paths, parameters, and verified dataset sources.
"""
import os
import random
import numpy as np
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

# Base project directory (assumes code/ is at repo root or one level down)
# We dynamically detect the project root by looking for the 'data' directory
def _find_project_root():
    current = Path(__file__).resolve()
    while current != current.parent:
        if (current / "data").exists():
            return current
        current = current.parent
    # Fallback: assume current working directory
    return Path.cwd()

PROJECT_ROOT = _find_project_root()

class Config:
    """Centralized configuration loading from data/processed/config.yaml."""
    
    def __init__(self):
        self._config_path = PROJECT_ROOT / "data" / "processed" / "config.yaml"
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self._config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found at {self._config_path}. "
                "Please run T011d to generate the pilot scope parameters."
            )
        
        with open(self._config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Ensure required keys exist with defaults for pilot mode
        required_keys = [
            'pilot_mode', 
            'expected_earthquake_count', 
            'moving_average_days',
            'min_permutation_iterations',
            'max_permutation_iterations',
            'convergence_variance_threshold'
        ]
        
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required configuration key: {key}")
        
        return config
    
    @property
    def pilot_mode(self) -> bool:
        return self._config.get('pilot_mode', True)
    
    @property
    def expected_earthquake_count(self) -> int:
        return int(self._config.get('expected_earthquake_count', 12))
    
    @property
    def moving_average_days(self) -> int:
        return int(self._config.get('moving_average_days', 30))
    
    @property
    def min_permutation_iterations(self) -> int:
        return int(self._config.get('min_permutation_iterations', 1000))
    
    @property
    def max_permutation_iterations(self) -> int:
        return int(self._config.get('max_permutation_iterations', 5000))
    
    @property
    def convergence_variance_threshold(self) -> float:
        return float(self._config.get('convergence_variance_threshold', 0.001))
    
    @property
    def usgs_base_url(self) -> str:
        return self._config.get('usgs_base_url', 'https://earthquake.usgs.gov/fdsnws/event/1/query')
    
    @property
    def test_region(self) -> str:
        return self._config.get('test_region', 'Alaska')
    
    @property
    def min_magnitude(self) -> float:
        return float(self._config.get('min_magnitude', 4.0))
    
    @property
    def max_depth_km(self) -> float:
        return float(self._config.get('max_depth_km', 70.0))

# Singleton instance
_config_instance = None

def get_config() -> Config:
    """Get the global configuration singleton."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

# Path helpers
def get_data_path() -> Path:
    """Get the data directory path."""
    return PROJECT_ROOT / "data"

def get_raw_path() -> Path:
    """Get the raw data directory path."""
    return get_data_path() / "raw"

def get_interim_path() -> Path:
    """Get the interim data directory path."""
    return get_data_path() / "interim"

def get_processed_path() -> Path:
    """Get the processed data directory path."""
    return get_data_path() / "processed"

def get_deviations_path() -> Path:
    """Get the deviations documentation path."""
    return PROJECT_ROOT / "docs" / "deviations.md"

# Parameter helpers
def get_event_window_days() -> int:
    """Get the event window duration in days (48 hours = 2 days)."""
    return 2

def get_control_window_days() -> int:
    """Get the control window duration in days."""
    return 30

def get_anomaly_window_days() -> int:
    """Get the anomaly baseline window duration in days."""
    return get_config().moving_average_days

# Random seed management
def get_random_seed() -> int:
    """Get the random seed for reproducibility."""
    return 42

def set_random_seed(seed: int):
    """Set the random seed for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)

# USGS API helpers
def get_usgs_base_url() -> str:
    """Get the USGS API base URL."""
    return get_config().usgs_base_url

def get_min_magnitude() -> float:
    """Get the minimum magnitude threshold."""
    return get_config().min_magnitude

def get_max_depth_km() -> float:
    """Get the maximum depth threshold in km."""
    return get_config().max_depth_km

def get_test_event_count() -> int:
    """Get the expected number of test events (from config)."""
    return get_config().expected_earthquake_count

def get_test_region() -> str:
    """Get the test region name."""
    return get_config().test_region
