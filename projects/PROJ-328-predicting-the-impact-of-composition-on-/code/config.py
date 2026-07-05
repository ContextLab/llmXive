"""
Environment configuration management for paths and thresholds.

This module provides centralized configuration for the solder hardness prediction pipeline,
handling directory paths, algorithmic thresholds, and runtime parameters.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

from utils.error_handlers import ConfigurationError

# Project Root
# Determines the root directory relative to the code/ folder
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Default configuration values
DEFAULT_CONFIG = {
    # Paths
    "data_raw_dir": "data/raw",
    "data_processed_dir": "data/processed",
    "data_outputs_dir": "data/outputs",
    "models_dir": "models",
    "specs_dir": "specs",
    
    # Thresholds & Hyperparameters
    "composition_sum_threshold": 0.95,  # Provisional per spec FR-002
    "max_elements": 5,
    "min_hardness_value": 0.0,
    "room_temp_tolerance_celsius": 5.0,  # +/- 5C around 25C
    
    # Model Parameters
    "cv_folds": 5,
    "bootstrap_iterations": 1000,
    "vif_threshold": 5.0,
    "r2_sensitivity_thresholds": [0.3, 0.5, 0.6, 0.7],
    
    # Ingestion
    "min_samples_warning": 50,
    "min_samples_target": 100,
    
    # Logging
    "log_level": "INFO",
    "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
}

class Config:
    """
    Singleton-like configuration manager.
    Loads settings from environment variables or uses defaults.
    """
    _instance: Optional['Config'] = None
    
    def __new__(cls) -> 'Config':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._config: Dict[str, Any] = {}
        self._base_path: Path = _PROJECT_ROOT
        self._load_config()
        self._initialized = True
    
    def _load_config(self):
        """Load configuration from environment variables or defaults."""
        # Start with defaults
        self._config = DEFAULT_CONFIG.copy()
        
        # Override with environment variables if present
        env_mapping = {
            "SOLDER_DATA_RAW": "data_raw_dir",
            "SOLDER_DATA_PROCESSED": "data_processed_dir",
            "SOLDER_DATA_OUTPUTS": "data_outputs_dir",
            "SOLDER_MODELS": "models_dir",
            "SOLDER_COMPOSITION_THRESHOLD": "composition_sum_threshold",
            "SOLDER_MAX_ELEMENTS": "max_elements",
            "SOLDER_VIF_THRESHOLD": "vif_threshold",
            "SOLDER_LOG_LEVEL": "log_level",
        }
        
        for env_key, config_key in env_mapping.items():
            value = os.getenv(env_key)
            if value is not None:
                # Attempt type conversion based on default type
                default_val = DEFAULT_CONFIG.get(config_key)
                try:
                    if isinstance(default_val, int):
                        self._config[config_key] = int(value)
                    elif isinstance(default_val, float):
                        self._config[config_key] = float(value)
                    elif isinstance(default_val, bool):
                        self._config[config_key] = value.lower() in ('true', '1', 'yes')
                    else:
                        self._config[config_key] = value
                except ValueError:
                    logging.warning(f"Could not convert env var {env_key} to type of default {config_key}. Using default.")
        
        # Resolve absolute paths for directories
        self._resolve_paths()
    
    def _resolve_paths(self):
        """Convert relative path strings to absolute Path objects."""
        path_keys = [
            "data_raw_dir",
            "data_processed_dir", 
            "data_outputs_dir",
            "models_dir",
            "specs_dir"
        ]
        
        for key in path_keys:
            if key in self._config:
                relative_path = self._config[key]
                if isinstance(relative_path, str):
                    self._config[key] = self._base_path / relative_path
                elif isinstance(relative_path, Path):
                    self._config[key] = self._base_path / relative_path
                else:
                    raise ConfigurationError(f"Invalid path type for {key}: {type(relative_path)}")
        
        # Ensure directories exist (optional, can be done at runtime)
        # self._ensure_directories()
    
    def _ensure_directories(self):
        """Create directory structure if it doesn't exist."""
        dirs_to_create = [
            self._config["data_raw_dir"],
            self._config["data_processed_dir"],
            self._config["data_outputs_dir"],
            self._config["models_dir"]
        ]
        
        for dir_path in dirs_to_create:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)
    
    def get_path(self, key: str) -> Path:
        """Get a configuration value as a Path object."""
        val = self._config.get(key)
        if val is None:
            raise ConfigurationError(f"Path configuration key '{key}' not found.")
        if not isinstance(val, Path):
            raise ConfigurationError(f"Configuration key '{key}' is not a Path object.")
        return val
    
    def get_int(self, key: str) -> int:
        val = self._config.get(key)
        if not isinstance(val, int):
            raise ConfigurationError(f"Configuration key '{key}' is not an integer.")
        return val
    
    def get_float(self, key: str) -> float:
        val = self._config.get(key)
        if not isinstance(val, float):
            raise ConfigurationError(f"Configuration key '{key}' is not a float.")
        return val
    
    def get_list(self, key: str) -> List:
        val = self._config.get(key)
        if not isinstance(val, list):
            raise ConfigurationError(f"Configuration key '{key}' is not a list.")
        return val

# Global config instance
config = Config()

# Convenience accessors
def get_data_raw_dir() -> Path:
    return config.get_path("data_raw_dir")

def get_data_processed_dir() -> Path:
    return config.get_path("data_processed_dir")

def get_data_outputs_dir() -> Path:
    return config.get_path("data_outputs_dir")

def get_models_dir() -> Path:
    return config.get_path("models_dir")

def get_composition_sum_threshold() -> float:
    return config.get_float("composition_sum_threshold")

def get_max_elements() -> int:
    return config.get_int("max_elements")

def get_vif_threshold() -> float:
    return config.get_float("vif_threshold")

def get_r2_sensitivity_thresholds() -> List[float]:
    return config.get_list("r2_sensitivity_thresholds")

def get_min_samples_warning() -> int:
    return config.get_int("min_samples_warning")

def get_min_samples_target() -> int:
    return config.get_int("min_samples_target")

def get_cv_folds() -> int:
    return config.get_int("cv_folds")

def get_bootstrap_iterations() -> int:
    return config.get_int("bootstrap_iterations")

def get_log_level() -> str:
    return config.get("log_level", "INFO")

def get_log_format() -> str:
    return config.get("log_format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

if __name__ == "__main__":
    # Simple test to verify configuration loads correctly
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info(f"Project Root: {config._base_path}")
    logger.info(f"Data Raw Dir: {get_data_raw_dir()}")
    logger.info(f"Data Processed Dir: {get_data_processed_dir()}")
    logger.info(f"Composition Sum Threshold: {get_composition_sum_threshold()}")
    logger.info(f"Max Elements: {get_max_elements()}")
    logger.info(f"VIF Threshold: {get_vif_threshold()}")
    logger.info(f"R2 Sensitivity Thresholds: {get_r2_sensitivity_thresholds()}")
    logger.info("Configuration loaded successfully.")