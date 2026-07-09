import os
from typing import Optional, Dict, Any
from pathlib import Path

class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""
    pass

# Default configuration values
DEFAULTS = {
    "DATASET_URL": "https://allen-brain-atlas-data.s3.amazonaws.com/visual-coding/sample_subset.h5",
    "RANDOM_SEED": 42,
    "MEMORY_LIMIT_GB": 5.0,  # Default limit per FR-001/SC-001
}

_config: Dict[str, Any] = {}

def init_config() -> None:
    """
    Initialize configuration from environment variables and defaults.
    Must be called before accessing config values.
    """
    global _config
    if _config:
        return
    
    _config = {}
    for key, default in DEFAULTS.items():
        env_val = os.getenv(key)
        if env_val is not None:
            _config[key] = env_val
        else:
            _config[key] = default

def get_config_value(key: str) -> Any:
    """Get a configuration value."""
    if not _config:
        init_config()
    if key not in _config:
        raise ConfigError(f"Configuration key '{key}' not found")
    return _config[key]

def get_dataset_url() -> str:
    """Get the dataset URL."""
    return str(get_config_value("DATASET_URL"))

def get_random_seed() -> int:
    """Get the random seed."""
    return int(get_config_value("RANDOM_SEED"))

def get_memory_limit_gb() -> float:
    """Get the memory limit in GB."""
    return float(get_config_value("MEMORY_LIMIT_GB"))

def get_all_config() -> Dict[str, Any]:
    """Get all configuration values."""
    if not _config:
        init_config()
    return _config.copy()
