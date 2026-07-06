"""
Environment configuration management for the heat transport analysis pipeline.

This module handles loading and validating configuration parameters from
environment variables, with sensible defaults and strict type checking.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from dotenv import load_dotenv

# Load .env file if it exists (optional, for local development)
load_dotenv()

# Default values
DEFAULT_CUTOFF_RADIUS = 3.0  # Angstroms
DEFAULT_ZENODO_URL = "https://zenodo.org/api/records/12345"  # Placeholder, to be overridden
DEFAULT_DATA_DIR = "data/raw"
DEFAULT_PROCESSED_DIR = "data/processed"
DEFAULT_LOG_LEVEL = "INFO"

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

class EnvironmentConfig:
    """
    Manages environment-based configuration for the pipeline.
    
    Attributes:
        cutoff_radius (float): Cutoff radius for graph construction in Angstroms.
        zenodo_url (str): Base URL for Zenodo dataset access.
        data_dir (Path): Path to raw data directory.
        processed_dir (Path): Path to processed data directory.
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR).
    """
    
    def __init__(self):
        self.cutoff_radius: float = self._get_float(
            "CUTOFF_RADIUS", DEFAULT_CUTOFF_RADIUS, 2.5, 4.0
        )
        self.zenodo_url: str = self._get_str(
            "ZENODO_URL", DEFAULT_ZENODO_URL
        )
        self.data_dir: Path = Path(self._get_str(
            "DATA_DIR", DEFAULT_DATA_DIR
        ))
        self.processed_dir: Path = Path(self._get_str(
            "PROCESSED_DIR", DEFAULT_PROCESSED_DIR
        ))
        self.log_level: str = self._get_str(
            "LOG_LEVEL", DEFAULT_LOG_LEVEL
        ).upper()
        
        # Validate paths exist or can be created
        self._ensure_directories()
    
    def _get_str(self, key: str, default: str) -> str:
        """Get a string environment variable with a default."""
        value = os.getenv(key)
        if value is None:
            return default
        return value.strip()
    
    def _get_float(self, key: str, default: float, min_val: float, max_val: float) -> float:
        """Get a float environment variable with validation."""
        value_str = os.getenv(key)
        if value_str is None:
            return default
        
        try:
            value = float(value_str)
        except ValueError:
            raise ConfigError(f"Environment variable {key} must be a float, got: {value_str}")
        
        if not (min_val <= value <= max_val):
            raise ConfigError(
                f"Environment variable {key}={value} is out of range [{min_val}, {max_val}]"
            )
        
        return value
    
    def _ensure_directories(self):
        """Ensure required data directories exist."""
        for dir_path in [self.data_dir, self.processed_dir]:
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    raise ConfigError(f"Failed to create directory {dir_path}: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as a dictionary."""
        return {
            "cutoff_radius": self.cutoff_radius,
            "zenodo_url": self.zenodo_url,
            "data_dir": str(self.data_dir),
            "processed_dir": str(self.processed_dir),
            "log_level": self.log_level
        }
    
    def __repr__(self) -> str:
        return f"EnvironmentConfig(cutoff_radius={self.cutoff_radius}, zenodo_url={self.zenodo_url})"

# Singleton instance for global access
_config_instance: Optional[EnvironmentConfig] = None

def get_config() -> EnvironmentConfig:
    """
    Get the singleton EnvironmentConfig instance.
    
    Returns:
        EnvironmentConfig: The global configuration instance.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = EnvironmentConfig()
    return _config_instance

def reload_config() -> EnvironmentConfig:
    """
    Force reload of the configuration (useful for testing).
    
    Returns:
        EnvironmentConfig: The new configuration instance.
    """
    global _config_instance
    _config_instance = EnvironmentConfig()
    return _config_instance

def get_cutoff_radius() -> float:
    """Convenience function to get cutoff radius."""
    return get_config().cutoff_radius

def get_zenodo_url() -> str:
    """Convenience function to get Zenodo URL."""
    return get_config().zenodo_url

def get_data_dir() -> Path:
    """Convenience function to get data directory."""
    return get_config().data_dir

def get_processed_dir() -> Path:
    """Convenience function to get processed data directory."""
    return get_config().processed_dir

def get_log_level() -> str:
    """Convenience function to get log level."""
    return get_config().log_level

if __name__ == "__main__":
    # Simple test/demo
    config = get_config()
    print("Configuration loaded:")
    print(f"  Cutoff Radius: {config.cutoff_radius} Å")
    print(f"  Zenodo URL: {config.zenodo_url}")
    print(f"  Data Dir: {config.data_dir}")
    print(f"  Processed Dir: {config.processed_dir}")
    print(f"  Log Level: {config.log_level}")
