import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union
import yaml

def get_project_root() -> Path:
    """Returns the root directory of the project."""
    return Path(__file__).resolve().parent.parent

def get_config() -> Dict[str, Any]:
    """Loads the main configuration file if it exists."""
    config_path = get_project_root() / "config.yaml"
    if config_path.exists():
        with open(config_path, "r") as f:
            return yaml.safe_load(f) or {}
    return {}

def get_config_value(key: str, default: Any = None) -> Any:
    """Retrieves a specific configuration value."""
    config = get_config()
    return config.get(key, default)

def get_random_state() -> int:
    """
    Returns a random seed for reproducibility.
    Prioritizes RANDOM_SEED env var, then config, then a fixed default.
    """
    env_seed = os.environ.get("RANDOM_SEED")
    if env_seed:
        return int(env_seed)
    
    config_seed = get_config_value("RANDOM_SEED")
    if config_seed is not None:
        return int(config_seed)
    
    return 42  # Default seed for reproducibility
