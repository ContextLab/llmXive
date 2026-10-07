"""
Configuration management for seeds, tolerances, and paths.

This module centralizes project-wide configuration parameters to ensure
reproducibility and ease of modification.
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional

# Project root is two levels up from this file (code/utils/config.py -> project root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_CONFIG_PATH = _PROJECT_ROOT / "code" / "config.json"

# Default values
_DEFAULTS = {
    "SEED": 42,
    "OUTLIER_TOLERANCE": 1e-10,
    "MAX_ITER": 1000,
    "DATA_PATH_RAW": "data/raw",
    "DATA_PATH_PROCESSED": "data/processed",
    "DATA_PATH_FIGURES": "data/figures",
    "DATA_PATH_LOGS": "data/logs",
    "STATE_PATH": "state",
}

_config_cache: Dict[str, Any] = {}


def _load_config() -> Dict[str, Any]:
    """Load configuration from file or return defaults."""
    if _config_cache:
        return _config_cache

    config = _DEFAULTS.copy()

    if _CONFIG_PATH.exists():
        try:
            with open(_CONFIG_PATH, 'r') as f:
                file_config = json.load(f)
                config.update(file_config)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load config file at {_CONFIG_PATH}: {e}. Using defaults.")
    else:
        # Create default config file if it doesn't exist
        _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=2)

    _config_cache.update(config)
    return config


def get_config(key: str, default: Any = None) -> Any:
    """
    Get a configuration value by key.

    Args:
        key: The configuration key.
        default: Default value if key is not found.

    Returns:
        The configuration value or default.
    """
    config = _load_config()
    return config.get(key, default)


def get_outlier_tolerance() -> float:
    """
    Get the outlier tolerance from configuration.

    Returns:
        The tolerance value (default 1e-10).
    """
    return float(get_config("OUTLIER_TOLERANCE", _DEFAULTS["OUTLIER_TOLERANCE"]))


def get_seed() -> int:
    """Get the random seed."""
    return int(get_config("SEED", _DEFAULTS["SEED"]))


def get_project_paths() -> Dict[str, Path]:
    """
    Get standardized paths for project directories.

    Returns:
        Dictionary mapping directory names to Path objects.
    """
    config = _load_config()
    paths = {}
    for key, default_path in _DEFAULTS.items():
        if key.startswith("DATA_PATH") or key == "STATE_PATH":
            # Handle relative paths from project root
            rel_path = config.get(key, default_path)
            paths[key] = _PROJECT_ROOT / rel_path
    return paths


def ensure_directories() -> None:
    """Ensure all required data directories exist."""
    paths = get_project_paths()
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)


def load_config_file(path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load a specific configuration file (optional override).

    Args:
        path: Path to a JSON config file. If None, uses the default project config.

    Returns:
        Configuration dictionary.
    """
    if path:
        cfg_path = Path(path)
    else:
        cfg_path = _CONFIG_PATH

    if cfg_path.exists():
        with open(cfg_path, 'r') as f:
            return json.load(f)
    return {}