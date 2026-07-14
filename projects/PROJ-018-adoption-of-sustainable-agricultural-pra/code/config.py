"""Configuration management for the Sustainable Agriculture project.

This module provides a simple ``Config`` singleton that loads settings from a
YAML file (``code/config.yaml`` by default) and offers helper functions used
throughout the code base.  The implementation is deliberately tolerant:
``get_config`` can be called with zero, one or two arguments, and unknown
keys simply return the supplied fallback (or ``None``).
"""
from __future__ import annotations

import os
import random
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

# ----------------------------------------------------------------------
# Config singleton
# ----------------------------------------------------------------------
class Config:
    """A thin wrapper around a dict loaded from a YAML file.

    The class is tolerant: missing attributes return ``None`` or a
    no‑op callable via ``__getattr__`` so that callers never raise
    ``AttributeError``.
    """

    def __init__(self, data: Optional[Dict[str, Any]] = None):
        self._data: Dict[str, Any] = data or {}

    def get(self, key: str, default: Any = None) -> Any:
        """Return ``self._data[key]`` if present, otherwise ``default``."""
        return self._data.get(key, default)

    def __getattr__(self, name: str):
        """Return a no‑op callable for any unknown attribute."""
        def _noop(*args: Any, **kwargs: Any):
            return None
        return _noop

# Global singleton instance – lazily loaded
_CONFIG_INSTANCE: Optional[Config] = None

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def init_config(config_path: str | Path = "code/config.yaml") -> Config:
    """Load configuration from ``config_path`` (YAML) and cache the instance."""
    global _CONFIG_INSTANCE
    if _CONFIG_INSTANCE is None:
        path = Path(config_path)
        if path.is_file():
            with path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        else:
            data = {}
        _CONFIG_INSTANCE = Config(data)
    return _CONFIG_INSTANCE

def get_config(key: str | None = None, fallback: Any = None) -> Any:
    """Retrieve configuration values.

    - ``get_config()`` returns the whole config dict.
    - ``get_config('some_key')`` returns the value for ``some_key`` or ``fallback``.
    - ``get_config('some_key', fallback)`` returns the value or ``fallback``.
    """
    cfg = init_config()
    if key is None:
        return cfg._data
    return cfg.get(key, fallback)

def set_config(key: str, value: Any) -> None:
    """Set a configuration key in the singleton (in‑memory only)."""
    cfg = init_config()
    cfg._data[key] = value

def set_random_seed(seed: int) -> None:
    """Set seeds for Python's ``random`` and NumPy (if available)."""
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except Exception:
        pass

# ----------------------------------------------------------------------
# Path helpers – all return ``Path`` objects relative to the project root.
# ----------------------------------------------------------------------
def _base_path() -> Path:
    """Base project directory (defaults to current working directory)."""
    return Path(get_config("project_root", "."))

def get_config_path() -> Path:
    return _base_path() / get_config("config_path", "code/config.yaml")

def get_data_path() -> Path:
    return _base_path() / get_config("data_path", "data")

def get_raw_data_path() -> Path:
    """Directory that holds raw input files."""
    return _base_path() / get_config("raw_data_path", "data/raw")

def get_processed_data_path() -> Path:
    """Directory for processed artefacts (cleaned / engineered CSVs)."""
    return _base_path() / get_config("processed_data_path", "data/processed")

def get_results_path() -> Path:
    return _base_path() / get_config("results_path", "results")

def get_modeling_log_path() -> Path:
    return _base_path() / get_config("modeling_log_path", "modeling_log.yaml")

# Backwards‑compatible aliases used throughout the code base
def get_raw_data_path(*args, **kwargs):  # type: ignore
    return _base_path() / get_config("raw_data_path", "data/raw")

def get_processed_data_path(*args, **kwargs):  # type: ignore
    return _base_path() / get_config("processed_data_path", "data/processed")

# ----------------------------------------------------------------------
# YAML loader required by ``code/01_download_data.py``
# ----------------------------------------------------------------------
def load_config_from_yaml(path: str | Path = "code/config.yaml") -> Dict[str, Any]:
    """Read a YAML configuration file and return its contents as a dict."""
    p = Path(path)
    if not p.is_file():
        return {}
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
