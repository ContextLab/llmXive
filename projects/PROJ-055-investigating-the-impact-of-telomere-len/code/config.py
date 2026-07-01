"""
Configuration management for the project.
"""
import os
import random
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import yaml

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

def init_config() -> Dict[str, Any]:
    """Initialize default configuration."""
    return {
        "dryad_api_key": os.getenv("DRYAD_API_KEY", ""),
        "anage_url": "https://api.ouranos.org/anage/birds.csv",
        "random_seed": 42,
        "paths": {
            "data_raw": "data/raw",
            "data_processed": "data/processed",
            "logs": "logs",
            "results": "results"
        }
    }

def load_env_config() -> Dict[str, Any]:
    """Load configuration from environment variables."""
    return {
        "dryad_api_key": os.getenv("DRYAD_API_KEY", ""),
        "anage_url": os.getenv("ANAGE_URL", "https://api.ouranos.org/anage/birds.csv"),
        "random_seed": int(os.getenv("RANDOM_SEED", "42"))
    }

def set_random_seed(seed: int) -> None:
    """Set random seed for reproducibility."""
    random.seed(seed)
    if 'numpy' in sys.modules:
        import numpy as np
        np.random.seed(seed)

def validate_config(config: Dict[str, Any]) -> bool:
    """Validate configuration values."""
    if not isinstance(config, dict):
        raise ConfigError("Config must be a dictionary")
    return True

def get_config() -> Dict[str, Any]:
    """Get the merged configuration."""
    base = init_config()
    env = load_env_config()
    base.update(env)
    validate_config(base)
    return base
