"""
Configuration management for the Sustainable Agricultural Practices project.

This module provides a centralized configuration system for:
- Data paths (raw, processed, results)
- Random seeds for reproducibility
- Project metadata
- Logging paths

Usage:
    config = get_config()  # Returns full Config object
    seed = get_config("random_seed", 42)  # Get specific value with default
    data_path = get_data_path()  # Helper for data directory
"""
from __future__ import annotations

import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml


class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass


class Config:
    """
    Configuration container that holds all project settings.

    This class provides dictionary-like access to configuration values
    and supports method chaining for common operations.
    """

    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """Initialize configuration from a dictionary."""
        self._config = config_dict or {}
        self._set_defaults()

    def _set_defaults(self) -> None:
        """Set default configuration values."""
        defaults = {
            "project_root": str(Path(__file__).parent.parent),
            "data_path": "data",
            "raw_data_path": "data/raw",
            "processed_data_path": "data/processed",
            "results_path": "results",
            "modeling_log_path": "modeling_log.yaml",
            "random_seed": 42,
            "n_respondents": 1000,
            "data_source": "synthetic_fallback",
            "country_codes": ["KEN", "UGA", "TZA", "ETH", "RWA"],
            "variable_validation_threshold": 0.95,
            "missing_value_threshold": 0.30,
            "power_analysis_threshold": 10,
            "vif_threshold": 5.0,
            "fdr_q_threshold": 0.10,
            "mediation_bootstrap_samples": 1000,
            "efa_factors_retained": "auto",
            "efa_extraction": "principal_axis",
            "efa_rotation": "varimax",
        }
        # Merge defaults with provided config (provided values override defaults)
        self._config.update(defaults)
        for key, value in self._config.items():
            if value is None:
                self._config[key] = defaults.get(key)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.

        Args:
            key: The configuration key to retrieve
            default: Default value if key doesn't exist

        Returns:
            The configuration value or default
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            key: The configuration key to set
            value: The value to set
        """
        self._config[key] = value

    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access: config['key']"""
        if key not in self._config:
            raise KeyError(f"Configuration key '{key}' not found")
        return self._config[key]

    def __contains__(self, key: str) -> bool:
        """Check if key exists in configuration."""
        return key in self._config

    def keys(self) -> list:
        """Return all configuration keys."""
        return list(self._config.keys())

    def items(self) -> list:
        """Return all key-value pairs."""
        return list(self._config.items())

    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as a dictionary."""
        return self._config.copy()

    def update(self, updates: Dict[str, Any]) -> None:
        """Update configuration with multiple key-value pairs."""
        self._config.update(updates)

    # Logger-style methods for compatibility with various call sites
    def info(self, *args: Any, **kwargs: Any) -> None:
        """No-op info method for compatibility."""
        pass

    def debug(self, *args: Any, **kwargs: Any) -> None:
        """No-op debug method for compatibility."""
        pass

    def warning(self, *args: Any, **kwargs: Any) -> None:
        """No-op warning method for compatibility."""
        pass

    def error(self, *args: Any, **kwargs: Any) -> None:
        """No-op error method for compatibility."""
        pass

    def critical(self, *args: Any, **kwargs: Any) -> None:
        """No-op critical method for compatibility."""
        pass

    def log(self, *args: Any, **kwargs: Any) -> None:
        """No-op log method for compatibility."""
        pass


# Global configuration instance
_global_config: Optional[Config] = None


def load_config_from_yaml(
    config_path: Optional[Union[str, Path]] = None
) -> Config:
    """
    Load configuration from a YAML file.

    Args:
        config_path: Path to the YAML configuration file.
                    If None, looks for 'config.yaml' in the project root.

    Returns:
        Config object with loaded settings

    Raises:
        ConfigError: If the file cannot be read or parsed
    """
    global _global_config

    if config_path is None:
        # Default location: project root / config.yaml
        project_root = Path(__file__).parent.parent
        config_path = project_root / "config.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        # Return default config if file doesn't exist
        _global_config = Config()
        return _global_config

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f) or {}
        _global_config = Config(config_dict)
    except yaml.YAMLError as e:
        raise ConfigError(f"Failed to parse YAML configuration: {e}")
    except IOError as e:
        raise ConfigError(f"Failed to read configuration file: {e}")

    return _global_config


def get_config(
    key: Optional[str] = None, default: Any = None
) -> Union[Config, Any]:
    """
    Get configuration value(s).

    This function supports three call patterns:
    1. get_config() -> Returns the full Config object
    2. get_config("key") -> Returns the value for "key" from config
    3. get_config("key", default) -> Returns the value for "key" or default

    Args:
        key: Optional configuration key to retrieve
        default: Default value if key doesn't exist (only used when key is provided)

    Returns:
        Either the full Config object or a specific configuration value
    """
    global _global_config

    # Initialize config if not already loaded
    if _global_config is None:
        _global_config = load_config_from_yaml()

    # If no key provided, return the full Config object
    if key is None:
        return _global_config

    # Otherwise, get the specific value
    return _global_config.get(key, default)


def set_random_seed(seed: Optional[int] = None) -> int:
    """
    Set the random seed for reproducibility.

    Args:
        seed: The random seed to use. If None, uses the value from config.

    Returns:
        The seed that was set
    """
    if seed is None:
        seed = get_config("random_seed", 42)

    random.seed(seed)
    # Also set numpy seed if available (for compatibility with downstream code)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass

    return seed


def get_config_path() -> Path:
    """
    Get the path to the configuration file.

    Returns:
        Path object pointing to the config.yaml file
    """
    project_root = Path(__file__).parent.parent
    return project_root / "config.yaml"


def get_data_path() -> Path:
    """
    Get the base data directory path.

    Returns:
        Path object pointing to the data directory
    """
    project_root = Path(get_config("project_root", "."))
    data_path = get_config("data_path", "data")
    return project_root / data_path


def get_raw_data_path() -> Path:
    """
    Get the raw data directory path.

    Returns:
        Path object pointing to the raw data directory
    """
    project_root = Path(get_config("project_root", "."))
    raw_data_path = get_config("raw_data_path", "data/raw")
    return project_root / raw_data_path


def get_processed_data_path() -> Path:
    """
    Get the processed data directory path.

    Returns:
        Path object pointing to the processed data directory
    """
    project_root = Path(get_config("project_root", "."))
    processed_data_path = get_config("processed_data_path", "data/processed")
    return project_root / processed_data_path


def get_results_path() -> Path:
    """
    Get the results directory path.

    Returns:
        Path object pointing to the results directory
    """
    project_root = Path(get_config("project_root", "."))
    results_path = get_config("results_path", "results")
    return project_root / results_path


def get_modeling_log_path() -> Path:
    """
    Get the path to the modeling log file.

    Returns:
        Path object pointing to the modeling_log.yaml file
    """
    project_root = Path(get_config("project_root", "."))
    log_path = get_config("modeling_log_path", "modeling_log.yaml")
    return project_root / log_path


# Ensure config is initialized on module import
load_config_from_yaml()