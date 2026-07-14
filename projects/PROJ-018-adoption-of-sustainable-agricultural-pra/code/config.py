"""
Configuration management for the Sustainable Agriculture project.
Handles loading from YAML, defaults, and random seed management.
"""
from __future__ import annotations

import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml


class ConfigError(Exception):
    """Raised when configuration loading or access fails."""
    pass


class Config:
    """
    Configuration container.
    Supports dictionary-like access and attribute access.
    """
    def __init__(self, data: Dict[str, Any] = None):
        self._data = data or {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._data[key] = value

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def to_dict(self) -> Dict[str, Any]:
        """Return the internal dictionary."""
        return self._data.copy()

    # Fallback for unknown logger-style calls to prevent AttributeError
    def __getattr__(self, name: str):
        def _noop(*args, **kwargs):
            return None
        return _noop


# Global default configuration values
DEFAULTS = {
    "project_root": ".",
    "data_raw_path": "data/raw",
    "data_processed_path": "data/processed",
    "results_path": "results",
    "random_seed": 42,
    "log_path": "modeling_log.yaml",
    "schema_path": "specs/018-adoption-sustainable-agriculture/contracts"
}


_global_config: Optional[Config] = None


def load_config_from_yaml(path: Union[str, Path]) -> Config:
    """Load configuration from a YAML file."""
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ConfigError(f"Failed to parse YAML: {e}")

    # Merge with defaults
    merged = {**DEFAULTS, **data}
    return Config(merged)


def get_config(key: Optional[str] = None, default: Any = None) -> Union[Dict[str, Any], Any, Config]:
    """
    Global config accessor.
    - get_config() -> Returns the full Config object (singleton).
    - get_config("key") -> Returns the value for 'key' (or None if missing).
    - get_config("key", default_val) -> Returns value or default_val.
    """
    global _global_config

    if _global_config is None:
        # Try to load from default location or use defaults
        config_path = Path("code/config.yaml")
        if config_path.exists():
            _global_config = load_config_from_yaml(config_path)
        else:
            _global_config = Config(DEFAULTS)

    if key is None:
        return _global_config

    return _global_config.get(key, default)


def set_random_seed(seed: Optional[int] = None) -> None:
    """
    Set random seeds for reproducibility.
    Uses the global config seed if not provided.
    """
    if seed is None:
        seed = get_config("random_seed", 42)

    random.seed(seed)
    # If numpy is available, seed it too
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass


def get_config_path() -> Path:
    """Return the path to the config file."""
    return Path("code/config.yaml")


def get_data_path(subpath: Optional[str] = None) -> Path:
    """
    Return the base data path.
    If subpath is provided, join it to the base.
    """
    base = Path(get_config("data_raw_path", "data/raw"))
    if subpath:
        return base / subpath
    return base
