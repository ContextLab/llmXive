"""
Configuration management for seeds, tolerances, and paths.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Project root is assumed to be the parent of the 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_CONFIG = {
    "seeds": {
        "default": 42,
        "sweep": [42, 123, 456, 789]
    },
    "tolerances": {
        "eigenvalue": 1e-10,
        "convergence": 1e-10
    },
    "paths": {
        "data_raw": "data/raw",
        "data_processed": "data/processed",
        "data_figures": "data/figures",
        "data_logs": "data/logs",
        "state": "state",
        "code": "code"
    }
}

def get_project_paths() -> Dict[str, Path]:
    """
    Return absolute paths for project directories relative to PROJECT_ROOT.

    Returns:
        Dict mapping logical names to absolute Path objects.
    """
    paths = {}
    for key, rel_path in DEFAULT_CONFIG["paths"].items():
        abs_path = PROJECT_ROOT / rel_path
        paths[key] = abs_path
    return paths

def get_config_value(key: str, default: Any = None) -> Any:
    """
    Retrieve a configuration value by key path (e.g., 'seeds.default').
    """
    keys = key.split(".")
    value = DEFAULT_CONFIG
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    return value

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from a JSON file if provided, otherwise return defaults.
    """
    if config_path and config_path.exists():
        with open(config_path, "r") as f:
            return json.load(f)
    return DEFAULT_CONFIG

def save_config(config: Dict[str, Any], config_path: Path) -> None:
    """Save configuration to a JSON file."""
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
