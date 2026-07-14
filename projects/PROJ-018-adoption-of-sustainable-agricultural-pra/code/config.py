"""Configuration management for the project."""
from __future__ import annotations

import os
import random
from pathlib import Path
from typing import Any, Dict, Optional
import yaml


DEFAULT_SEED = 42


class Config:
    """Configuration container with dictionary-like access."""

    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        self._data = config_dict or {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._data[key] = value

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def __getattr__(self, name: str) -> Any:
        # Fallback for attribute-style access
        if name in self._data:
            return self._data[name]
        raise AttributeError(f"'Config' object has no attribute '{name}'")


def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from a YAML file."""
    if config_path is None:
        config_path = "code/config.yaml"

    path = Path(config_path)
    if path.exists():
        with open(path, "r") as f:
            config_dict = yaml.safe_load(f) or {}
    else:
        config_dict = {}

    # Set defaults
    if "random_seed" not in config_dict:
        config_dict["random_seed"] = DEFAULT_SEED
    if "project_root" not in config_dict:
        config_dict["project_root"] = str(Path(__file__).parent.parent)

    # Ensure data paths exist
    data_root = Path(config_dict.get("project_root", ".")) / "data"
    raw_path = data_root / "raw"
    processed_path = data_root / "processed"
    results_path = data_root / "results"

    config_dict.setdefault("raw_data_path", str(raw_path))
    config_dict.setdefault("processed_data_path", str(processed_path))
    config_dict.setdefault("results_path", str(results_path))

    # Create directories if they don't exist
    for p in [raw_path, processed_path, results_path]:
        Path(p).mkdir(parents=True, exist_ok=True)

    return Config(config_dict)


_GLOBAL_CONFIG: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _GLOBAL_CONFIG
    if _GLOBAL_CONFIG is None:
        _GLOBAL_CONFIG = load_config()
    return _GLOBAL_CONFIG


def set_random_seed(seed: Optional[int] = None) -> None:
    """Set random seed for reproducibility."""
    if seed is None:
        seed = get_config().get("random_seed", DEFAULT_SEED)
    random.seed(seed)


def get_data_path() -> Path:
    """Get the data root path."""
    return Path(get_config().get("project_root", ".")) / "data"


def get_config_path() -> Path:
    """Get the config file path."""
    return Path("code/config.yaml")


def get_raw_data_path() -> Path:
    """Get the raw data path."""
    return Path(get_config().get("raw_data_path", "data/raw"))


def get_processed_data_path() -> Path:
    """Get the processed data path."""
    return Path(get_config().get("processed_data_path", "data/processed"))


def get_results_path() -> Path:
    """Get the results path."""
    return Path(get_config().get("results_path", "data/results"))
