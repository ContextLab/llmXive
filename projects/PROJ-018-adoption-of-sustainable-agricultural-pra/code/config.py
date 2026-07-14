"""
Base configuration management for data paths and random seeds.

This module provides a centralized configuration system for the project,
handling data paths, random seeds for reproducibility, and project settings.
"""
from __future__ import annotations

import os
import random
from pathlib import Path
from typing import Any, Dict, Optional
import yaml


class ConfigError(Exception):
    """Custom exception for configuration-related errors."""
    pass


class Config:
    """Centralized configuration manager for the project."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration.

        Args:
            config_path: Path to the YAML configuration file. If None,
                        looks for 'config.yaml' in the code directory.
        """
        # Determine project root (parent of 'code' directory)
        self.code_dir = Path(__file__).parent
        self.project_root = self.code_dir.parent

        # Default config path
        if config_path is None:
            self.config_path = self.code_dir / "config.yaml"
        else:
            self.config_path = Path(config_path)

        # Initialize default settings
        self._settings: Dict[str, Any] = {
            "random_seed": 42,
            "data_paths": {
                "raw": self.project_root / "data" / "raw",
                "processed": self.project_root / "data" / "processed",
                "results": self.project_root / "results",
                "figures": self.project_root / "results" / "figures",
            },
            "logging": {
                "log_file": self.code_dir / "modeling_log.yaml",
                "level": "INFO",
            },
            "analysis": {
                "min_sample_size": 30,
                "power_threshold": 0.80,
                "alpha_level": 0.05,
                "fdr_q_threshold": 0.10,
            },
            "modeling": {
                "vif_threshold": 5.0,
                "min_events_per_predictor": 10,
                "bootstrap_resamples": 1000,
                "efa_extraction": "Principal Axis Factoring",
                "efa_rotation": "Varimax",
                "efa_eigenvalue_threshold": 1.0,
            },
            "data_sources": {
                "world_bank_lsms_url": None,  # Will be set if available
                "fao_fies_url": None,        # Will be set if available
                "use_synthetic_fallback": True,
            },
        }

        # Load from file if it exists
        if self.config_path.exists():
            self._load_from_file()

        # Ensure directories exist
        self._ensure_directories()

    def _load_from_file(self) -> None:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                file_config = yaml.safe_load(f) or {}

            # Merge file config with defaults
            self._merge_config(self._settings, file_config)

        except yaml.YAMLError as e:
            raise ConfigError(f"Failed to parse config file {self.config_path}: {e}")
        except IOError as e:
            raise ConfigError(f"Failed to read config file {self.config_path}: {e}")

    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Recursively merge override dict into base dict."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        paths_to_create = [
            self._settings["data_paths"]["raw"],
            self._settings["data_paths"]["processed"],
            self._settings["data_paths"]["results"],
            self._settings["data_paths"]["figures"],
        ]

        for path in paths_to_create:
            path.mkdir(parents=True, exist_ok=True)

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

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value using dot notation.

        Args:
            key: Dot-separated key path (e.g., "random_seed")
            value: The value to set.
        """
        keys = key.split(".")
        current = self._settings

        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        # Set the final key
        current[keys[-1]] = value

    def get_data_path(self, path_type: str = "processed") -> Path:
        """
        Get a specific data path.

        Args:
            path_type: One of 'raw', 'processed', 'results', 'figures'

        Returns:
            Path object for the requested directory.
        """
        return Path(self._settings["data_paths"].get(path_type, ""))

    def get_config_path(self) -> Path:
        """Get the path to the configuration file."""
        return self.config_path

    def set_random_seed(self, seed: int) -> None:
        """
        Set the random seed for reproducibility.

        Args:
            seed: Integer seed value.
        """
        if not isinstance(seed, int) or seed < 0:
            raise ConfigError("Random seed must be a non-negative integer.")

        self._settings["random_seed"] = seed
        random.seed(seed)

        # Also set numpy seed if available
        try:
            import numpy as np
            np.random.seed(seed)
        except ImportError:
            pass  # numpy not required for config

    def get_random_seed(self) -> int:
        """Get the current random seed."""
        return self._settings["random_seed"]

    def save(self, path: Optional[Path] = None) -> None:
        """
        Save current configuration to YAML file.

        Args:
            path: Optional path to save to. If None, uses default config path.
        """
        save_path = Path(path) if path else self.config_path

        try:
            with open(save_path, "w", encoding="utf-8") as f:
                yaml.dump(self._settings, f, default_flow_style=False, sort_keys=False)
        except IOError as e:
            raise ConfigError(f"Failed to write config file {save_path}: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """Return a copy of the current settings as a dictionary."""
        import copy
        return copy.deepcopy(self._settings)


# Global configuration instance
_global_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance.

    Returns:
        The global Config instance, creating it if necessary.
    """
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config


def set_random_seed(seed: int) -> None:
    """
    Set the random seed in the global configuration.

    Args:
        seed: Integer seed value.
    """
    config = get_config()
    config.set_random_seed(seed)


def get_data_path(path_type: str = "processed") -> Path:
    """
    Get a data path from the global configuration.

    Args:
        path_type: One of 'raw', 'processed', 'results', 'figures'

    Returns:
        Path object for the requested directory.
    """
    config = get_config()
    return config.get_data_path(path_type)


def get_config_path() -> Path:
    """
    Get the configuration file path from the global configuration.

    Returns:
        Path object for the config file.
    """
    config = get_config()
    return config.get_config_path()


# Initialize config on module import
get_config()