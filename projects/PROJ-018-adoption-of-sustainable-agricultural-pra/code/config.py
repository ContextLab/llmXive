"""Configuration management for the project."""
from __future__ import annotations

import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, Union
import yaml


class ConfigError(Exception):
    """Raised when configuration loading fails."""
    pass


class Config:
    """Configuration holder with tolerant attribute access.

    Allows both dict-style access (get) and attribute-style access.
    Also provides a tolerant __getattr__ for any logger-like calls.
    """

    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        self._config = config_dict or {}
        self._set_defaults()

    def _set_defaults(self):
        """Set default configuration values."""
        defaults = {
            "project_root": ".",
            "data_path": "data",
            "raw_data_path": "data/raw",
            "processed_data_path": "data/processed",
            "results_path": "results",
            "figures_path": "figures",
            "modeling_log_path": "modeling_log.yaml",
            "random_seed": 42,
            "n_respondents": 1000,
            "proxy_variables": [
                "community_membership",
                "extension_contact",
                "collective_action",
                "knowledge_exchange"
            ],
            "engagement_weights": {}
        }
        for key, value in defaults.items():
            if key not in self._config:
                self._config[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            The configuration value or default
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key
            value: Value to set
        """
        self._config[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """Return the configuration as a dictionary."""
        return self._config.copy()

    # Tolerant for any other method call (e.g., .info/.debug/.warning/.error/...)
    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop

    def __getitem__(self, key: str) -> Any:
        return self._config[key]

    def __contains__(self, key: str) -> bool:
        return key in self._config


_global_config: Optional[Config] = None


def load_config_from_yaml(config_path: str) -> Config:
    """Load configuration from a YAML file.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        Config object

    Raises:
        ConfigError: If file cannot be loaded or parsed
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)
        return Config(config_dict)
    except Exception as e:
        raise ConfigError(f"Failed to load config from {config_path}: {e}")


def get_config(key: Optional[str] = None, default: Any = None) -> Union[Config, Any]:
    """Get the global configuration or a specific value from it.

    This function supports multiple call patterns:
    1. get_config() -> Returns the full Config object
    2. get_config("key") -> Returns the value for "key" from config
    3. get_config("key", default) -> Returns the value for "key" or default

    Args:
        key: Optional configuration key
        default: Default value if key not found (only used when key is provided)

    Returns:
        Config object if no key provided, otherwise the configuration value
    """
    global _global_config
    if _global_config is None:
        # Try to load from default location
        default_path = "code/config.yaml"
        if os.path.exists(default_path):
            _global_config = load_config_from_yaml(default_path)
        else:
            _global_config = Config()

    if key is None:
        return _global_config
    else:
        return _global_config.get(key, default)


def set_config(config: Config) -> None:
    """Set the global configuration.

    Args:
        config: Config object to set as global
    """
    global _global_config
    _global_config = config


def set_random_seed(seed: int) -> None:
    """Set the random seed for reproducibility.

    Args:
        seed: Random seed value
    """
    random.seed(seed)
    # Also update config if it exists
    if _global_config:
        _global_config.set("random_seed", seed)


def get_config_path() -> str:
    """Get the configuration file path.

    Returns:
        Path to the configuration file
    """
    return get_config("config_path", "code/config.yaml")


def get_data_path(default: str = "data") -> Path:
    """Get the data directory path.

    Args:
        default: Default path if not configured

    Returns:
        Path object for data directory
    """
    base = get_config("project_root", ".")
    return Path(base) / get_config("data_path", default)


def get_raw_data_path(default: str = "data/raw") -> Path:
    """Get the raw data directory path.

    Args:
        default: Default path if not configured

    Returns:
        Path object for raw data directory
    """
    base = get_config("project_root", ".")
    return Path(base) / get_config("raw_data_path", default)


def get_processed_data_path(default: str = "data/processed") -> Path:
    """Get the processed data directory path.

    Args:
        default: Default path if not configured

    Returns:
        Path object for processed data directory
    """
    base = get_config("project_root", ".")
    return Path(base) / get_config("processed_data_path", default)


def get_results_path(default: str = "results") -> Path:
    """Get the results directory path.

    Args:
        default: Default path if not configured

    Returns:
        Path object for results directory
    """
    base = get_config("project_root", ".")
    return Path(base) / get_config("results_path", default)


def get_figures_path(default: str = "figures") -> Path:
    """Get the figures directory path.

    Args:
        default: Default path if not configured

    Returns:
        Path object for figures directory
    """
    base = get_config("project_root", ".")
    return Path(base) / get_config("figures_path", default)


def get_modeling_log_path(default: str = "modeling_log.yaml") -> Path:
    """Get the modeling log file path.

    Args:
        default: Default path if not configured

    Returns:
        Path object for modeling log file
    """
    base = get_config("project_root", ".")
    return Path(base) / get_config("modeling_log_path", default)
