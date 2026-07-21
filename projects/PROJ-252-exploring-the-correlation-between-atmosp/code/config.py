"""
Configuration management for the project.
"""
import os
import random
import numpy as np
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
CODE_DIR = BASE_DIR / "code"
DOCS_DIR = BASE_DIR / "docs"
CONTRACTS_DIR = BASE_DIR / "contracts"

# Configuration defaults
DEFAULT_CONFIG = {
    "random_seed": 42,
    "usgs_base_url": "https://earthquake.usgs.gov/fdsnws/event/1/query",
    "min_magnitude": 4.0,
    "max_depth_km": 70.0,
    "test_event_count": 12,
    "test_region": "Alaska",
    "event_window_days": 30,
    "control_window_days": 30,
    "anomaly_window_days": 30,
    "deviations_path": "docs/deviations.md",
    "processed_path": "data/processed",
    "raw_path": "data/raw",
    "interim_path": "data/interim"
}

class Config:
    """Configuration class to manage project settings."""
    
    def __init__(self):
        self._config = DEFAULT_CONFIG.copy()
        self._load_config_from_file()
    
    def _load_config_from_file(self):
        """Load configuration from a YAML file if it exists."""
        config_path = CODE_DIR / "config.yaml"
        if config_path.exists():
            with open(config_path, 'r') as f:
                file_config = yaml.safe_load(f)
                if file_config:
                    self._config.update(file_config)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set a configuration value."""
        self._config[key] = value

# Global config instance
_config = Config()

def get_data_path() -> Path:
    """Get the base data directory."""
    return DATA_DIR

def get_raw_path(filename: str = "") -> Path:
    """Get the raw data directory or a specific file path."""
    path = DATA_DIR / "raw"
    if filename:
        path = path / filename
    return path

def get_interim_path(filename: str = "") -> Path:
    """Get the interim data directory or a specific file path."""
    path = DATA_DIR / "interim"
    if filename:
        path = path / filename
    return path

def get_processed_path(filename: str = "") -> Path:
    """Get the processed data directory or a specific file path."""
    path = DATA_DIR / "processed"
    if filename:
        path = path / filename
    return path

def get_deviations_path() -> Path:
    """Get the path to the deviations document."""
    return DOCS_DIR / "deviations.md"

def get_event_window_days() -> int:
    """Get the event window duration in days."""
    return _config.get("event_window_days", 30)

def get_control_window_days() -> int:
    """Get the control window duration in days."""
    return _config.get("control_window_days", 30)

def get_anomaly_window_days() -> int:
    """Get the anomaly calculation window duration in days."""
    return _config.get("anomaly_window_days", 30)

def get_random_seed() -> int:
    """Get the random seed for reproducibility."""
    return _config.get("random_seed", 42)

def set_random_seed(seed: int):
    """Set the random seed for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    _config.set("random_seed", seed)

def get_usgs_base_url() -> str:
    """Get the USGS API base URL."""
    return _config.get("usgs_base_url", "https://earthquake.usgs.gov/fdsnws/event/1/query")

def get_min_magnitude() -> float:
    """Get the minimum magnitude threshold."""
    return _config.get("min_magnitude", 4.0)

def get_max_depth_km() -> float:
    """Get the maximum depth threshold in km."""
    return _config.get("max_depth_km", 70.0)

def get_test_event_count() -> int:
    """Get the expected number of test events."""
    return _config.get("test_event_count", 12)

def get_test_region() -> str:
    """Get the test region name."""
    return _config.get("test_region", "Alaska")
