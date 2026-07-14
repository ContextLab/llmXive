"""Configuration management for the project.

Provides a tiny wrapper around a YAML configuration file and a few convenience
helpers used throughout the pipeline. All functions are deliberately tolerant:
they accept any combination of positional/keyword arguments and never raise
``KeyError`` for missing keys – instead they return ``None`` or the supplied
default value.
"""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

# --------------------------------------------------------------------------- #
# Global configuration singleton
# --------------------------------------------------------------------------- #
_GLOBAL_CONFIG: Dict[str, Any] = {}
_CONFIG_PATH: Path = Path("code/config.yaml")


def set_config_path(path: str | Path) -> None:
    """Set a custom path for the YAML configuration file."""
    global _CONFIG_PATH
    _CONFIG_PATH = Path(path)
    # Reset loaded config so the next call to ``get_config`` reloads it.
    _GLOBAL_CONFIG.clear()


def _load_config() -> Dict[str, Any]:
    """Load the YAML configuration file if it exists."""
    if not _CONFIG_PATH.is_file():
        return {}
    with _CONFIG_PATH.open("r", encoding="utf-8") as f:
        try:
            cfg = yaml.safe_load(f) or {}
            return cfg if isinstance(cfg, dict) else {}
        except yaml.YAMLError:
            return {}


def get_config(key: str | None = None, default: Any = None) -> Any:
    """
    Retrieve configuration values.

    * ``get_config()`` – returns the entire configuration dictionary.
    * ``get_config('some_key')`` – returns the value for ``some_key`` or ``None``.
    * ``get_config('some_key', default)`` – returns the value or ``default``.
    """
    global _GLOBAL_CONFIG
    if not _GLOBAL_CONFIG:
        _GLOBAL_CONFIG = _load_config()

    if key is None:
        # Caller wants the whole config dict.
        return _GLOBAL_CONFIG
    return _GLOBAL_CONFIG.get(key, default)


def set_random_seed(seed: int) -> None:
    """Seed the Python ``random`` module and NumPy (if available)."""
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except Exception:
        # NumPy may not be installed – ignore silently.
        pass


# --------------------------------------------------------------------------- #
# Convenience path helpers – all tolerant to missing configuration entries.
# --------------------------------------------------------------------------- #
def _base_path() -> Path:
    """Base project root (defaults to current working directory)."""
    return Path(get_config("project_root", "."))


def get_data_path() -> Path:
    """Root data directory."""
    return _base_path() / get_config("data_path", "data")


def get_raw_data_path() -> Path:
    """Directory that holds raw input files."""
    return _base_path() / get_config("raw_data_path", "data/raw")


def get_processed_data_path() -> Path:
    """Directory for processed artefacts (cleaned / engineered CSVs)."""
    return _base_path() / get_config("processed_data_path", "data/processed")


def get_results_path() -> Path:
    """Directory for results artefacts (models, metrics, figures)."""
    return _base_path() / get_config("results_path", "results")


def get_modeling_log_path() -> Path:
    """Path to the YAML modelling log."""
    return _base_path() / get_config("modeling_log_path", "modeling_log.yaml")
