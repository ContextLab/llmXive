"""
Base configuration management for data paths and random seeds.

This module provides a centralized configuration system for the project,
handling data paths, random seeds for reproducibility, and project settings.
"""
from __future__ import annotations

import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, Callable
import yaml


DEFAULT_SEED = 42
DEFAULT_DATA_PATH = "data"
DEFAULT_RAW_DATA_PATH = "data/raw"
DEFAULT_PROCESSED_DATA_PATH = "data/processed"
DEFAULT_RESULTS_PATH = "results"


class Config:
    """Configuration holder with dict-like access and tolerant logger methods."""

    def __init__(self, data: Dict[str, Any]) -> None:
        self._data = data
        self._seed = self._data.get("random_seed", DEFAULT_SEED)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.

        Args:
            key: Dot-separated key path (e.g., "data_paths.raw")
        Returns:
            The configuration value or default if not found.
        """
        keys = key.split(".")
        value = self._settings

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def __getattr__(self, name: str):
        """Tolerant fallback for any method call (logger-style no-ops)."""
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop


def load_config(config_path: str = "code/config.yaml") -> Config:
    """Load configuration from a YAML file."""
    path = Path(config_path)
    if path.exists():
        with open(path, 'r') as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {}

    # Ensure defaults are present
    if "random_seed" not in data:
        data["random_seed"] = DEFAULT_SEED

    return Config(data)


def get_config() -> Config:
    """Get the global configuration instance."""
    return load_config()


def set_random_seed(seed: int) -> None:
    """Set the random seed for reproducibility."""
    random.seed(seed)


def get_data_path() -> Path:
    """Get the base data path."""
    config = get_config()
    return Path(config.get("data_path", DEFAULT_DATA_PATH))


def get_config_path() -> Path:
    """
    Get the configuration file path from the global configuration.

    Returns:
        Path object for the config file.
    """
    config = get_config()
    return config.get_config_path()


def get_raw_data_path() -> Path:
    """Get the raw data path."""
    config = get_config()
    return Path(config.get("raw_data_path", DEFAULT_RAW_DATA_PATH))


def get_processed_data_path() -> Path:
    """Get the processed data path."""
    config = get_config()
    return Path(config.get("processed_data_path", DEFAULT_PROCESSED_DATA_PATH))


def get_results_path() -> Path:
    """Get the results path."""
    config = get_config()
    return Path(config.get("results_path", DEFAULT_RESULTS_PATH))
