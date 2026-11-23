"""
Configuration management for the Calibration Drift project.
Handles path resolution, directory creation, and configuration loading.
"""
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

# Project root is assumed to be the parent of the 'code' directory
# Or we can use an environment variable if set
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

def get_config_dict(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    Falls back to default settings if no file is provided or file is missing.
    """
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    # Default configuration
    return {
        "data": {
            "raw": "data/raw",
            "processed": "data/processed",
            "models": "data/models",
            "figures": "figures"
        },
        "params": {
            "random_state": 42,
            "test_size": 0.2
        }
    }

def get_path(key: str) -> Path:
    """
    Resolve a project path based on a key from the configuration.
    Keys are dot-separated (e.g., 'data.processed').
    """
    config = get_config_dict()
    
    parts = key.split('.')
    value = config
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part)
        else:
            raise KeyError(f"Invalid config key: {key}. Path segment '{part}' not found.")
    
    if not value:
        raise KeyError(f"Config key '{key}' not found or is empty.")
    
    # If the value is a relative path, join with project root
    if isinstance(value, str):
        return _PROJECT_ROOT / value
    return Path(value)

def ensure_directories() -> None:
    """
    Create all necessary directories defined in the configuration.
    """
    config = get_config_dict()
    paths_to_create = [
        "data.raw",
        "data.processed",
        "data.models",
        "figures",
        "tests.unit",
        "tests.integration"
    ]
    
    for path_key in paths_to_create:
        try:
            path = get_path(path_key)
            path.mkdir(parents=True, exist_ok=True)
        except KeyError:
            # Ignore if key doesn't exist in config
            pass
