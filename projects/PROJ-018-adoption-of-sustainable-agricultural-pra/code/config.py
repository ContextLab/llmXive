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
    Configuration manager that loads settings from a YAML file and provides
    convenient access to configuration values.
    """

    def __init__(self, config_dict: Dict[str, Any]):
        self._config = config_dict

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.

        Args:
            key: The configuration key to look up.
            default: Default value to return if key is not found.

        Returns:
            The configuration value or default.
        """
        return self._config.get(key, default)

    def keys(self) -> list:
        """Return all configuration keys."""
        return list(self._config.keys())

    def items(self) -> list:
        """Return all key-value pairs."""
        return list(self._config.items())

    def __getattr__(self, name: str) -> Any:
        """Allow attribute-style access to config keys."""
        if name in self._config:
            return self._config[name]
        raise AttributeError(f"Configuration Key '{name}' not found")

    def __repr__(self) -> str:
        return f"Config({self._config})"


def load_config_from_yaml(config_path: Union[str, Path]) -> Config:
    """
    Load configuration from a YAML file.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        Config object containing the loaded settings.

    Raises:
        ConfigError: If the file cannot be read or parsed.
    """
    try:
        path = Path(config_path)
        if not path.exists():
            raise ConfigError(f"Config file not found: {config_path}")

        with open(path, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f) or {}

        return Config(config_dict)
    except yaml.YAMLError as e:
        raise ConfigError(f"Failed to parse YAML config: {e}")
    except Exception as e:
        raise ConfigError(f"Failed to load config from {config_path}: {e}")


# Global config instance (lazy initialization)
_global_config: Optional[Config] = None
_config_path: Optional[Path] = None


def get_config(key: Optional[str] = None, default: Any = None) -> Union[Config, Any]:
    """
    Get the global configuration object or a specific value from it.

    This function supports multiple calling patterns:
    - get_config() -> Returns the full Config object
    - get_config("key") -> Returns the value for "key" from config
    - get_config("key", default) -> Returns the value for "key" or default

    Args:
        key: Optional key to retrieve a specific value.
        default: Default value if key is not found (only used when key is provided).

    Returns:
        Either the full Config object or a specific value.
    """
    global _global_config, _config_path

    if _global_config is None:
        # Try to find config file in standard locations
        possible_paths = [
            Path("config.yaml"),
            Path("data", "config.yaml"),
            Path("code", "config.yaml"),
            Path("..", "config.yaml"),
        ]

        for p in possible_paths:
            if p.exists():
                _config_path = p
                _global_config = load_config_from_yaml(p)
                break

        if _global_config is None:
            # Create a default config if no file found
            _global_config = Config({
                "project_root": str(Path.cwd()),
                "data_path": str(Path.cwd() / "data"),
                "raw_data_path": str(Path.cwd() / "data" / "raw"),
                "processed_data_path": str(Path.cwd() / "data" / "processed"),
                "results_path": str(Path.cwd() / "results"),
                "random_seed": 42,
                "modeling_log_path": str(Path.cwd() / "modeling_log.yaml"),
            })

    if key is None:
        return _global_config

    return _global_config.get(key, default)


def set_random_seed(seed: Optional[int] = None) -> None:
    """
    Set the random seed for reproducibility.

    This function initializes seeds for:
    - Python's built-in random module
    - NumPy (if available)
    - Python's hash seed (via environment variable)

    Args:
        seed: The seed value. If None, uses the value from config.
    """
    if seed is None:
        seed = get_config("random_seed", 42)

    # Set seed for Python's random module
    random.seed(seed)
    
    # Set seed for NumPy if available
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass  # NumPy not available, skip

    # Set PYTHONHASHSEED for reproducibility in string hashing
    os.environ['PYTHONHASHSEED'] = str(seed)


def get_config_path() -> Optional[Path]:
    """Return the path to the loaded configuration file."""
    return _config_path


def get_data_path() -> Path:
    """Return the base data path from configuration."""
    return Path(get_config("data_path", "data"))


def get_raw_data_path() -> Path:
    """Return the raw data path from configuration."""
    return Path(get_config("raw_data_path", "data/raw"))


def get_processed_data_path() -> Path:
    """Return the processed data path from configuration."""
    return Path(get_config("processed_data_path", "data/processed"))


def get_results_path() -> Path:
    """Return the results path from configuration."""
    return Path(get_config("results_path", "results"))


def get_modeling_log_path() -> Path:
    """Return the modeling log path from configuration."""
    return Path(get_config("modeling_log_path", "modeling_log.yaml"))
