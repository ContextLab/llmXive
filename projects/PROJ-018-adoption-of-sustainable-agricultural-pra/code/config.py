"""
Configuration management for the sustainable agriculture adoption study.

This module provides centralized configuration for:
- Data paths (raw, processed, results)
- Random seeds for reproducibility
- Project directory structure
"""
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

# Project root directory (relative to where this script is run)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Default configuration values
DEFAULTS: Dict[str, Any] = {
    "random_seed": 42,
    "paths": {
        "data_raw": "data/raw",
        "data_processed": "data/processed",
        "data_results": "results",
        "code": "code",
        "specs": "specs/018-adoption-sustainable-agriculture",
        "tests": "tests",
        "docs": "docs",
    },
    "logging": {
        "log_file": "modeling_log.yaml",
        "log_level": "INFO",
    },
    "synthetic_data": {
        "n_samples": 1000,
        "low_income_country_codes": ["BD", "ET", "IN", "KE", "NG", "PK", "TZ", "UG"],
    },
    "modeling": {
        "test_size": 0.2,
        "fdr_threshold": 0.10,
        "vif_threshold": 5.0,
        "min_power_ratio": 10.0,
    },
}

class Config:
    """
    Centralized configuration manager for the project.

    Handles loading, validation, and access to all project configuration
    including paths, seeds, and modeling parameters.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration.

        Args:
            config_path: Optional path to a custom config YAML file.
                        If not provided, uses defaults.
        """
        self._config = DEFAULTS.copy()
        self._config_path = config_path or (PROJECT_ROOT / "config.yaml")

        if config_path and config_path.exists():
            self._load_from_file(config_path)

        self._ensure_directories()

    def _load_from_file(self, path: Path) -> None:
        """Load configuration from a YAML file."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                custom_config = yaml.safe_load(f) or {}

            # Deep merge custom config with defaults
            self._deep_merge(self._config, custom_config)
        except Exception as e:
            raise RuntimeError(f"Failed to load config from {path}: {e}")

    def _deep_merge(self, base: Dict, override: Dict) -> None:
        """Recursively merge override dict into base dict."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def _ensure_directories(self) -> None:
        """Create all required directories if they don't exist."""
        paths = self.get("paths", {})
        for dir_name in paths.values():
            dir_path = PROJECT_ROOT / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)

    @property
    def random_seed(self) -> int:
        """Get the random seed for reproducibility."""
        return self._config["random_seed"]

    @random_seed.setter
    def random_seed(self, value: int) -> None:
        """Set the random seed and update global random state."""
        self._config["random_seed"] = value
        random.seed(value)
        # Also set numpy seed if available
        try:
            import numpy as np
            np.random.seed(value)
        except ImportError:
            pass

    def set_random_seed(self, seed: int) -> None:
        """Convenience method to set random seed."""
        self.random_seed = seed

    def get_path(self, key: str) -> Path:
        """
        Get a project path by key.

        Args:
            key: Key from the paths configuration (e.g., 'data_raw', 'results')

        Returns:
            Absolute Path object
        """
        relative_path = self._config["paths"].get(key, "")
        return PROJECT_ROOT / relative_path

    @property
    def data_raw_dir(self) -> Path:
        """Path to raw data directory."""
        return self.get_path("data_raw")

    @property
    def data_processed_dir(self) -> Path:
        """Path to processed data directory."""
        return self.get_path("data_processed")

    @property
    def results_dir(self) -> Path:
        """Path to results directory."""
        return self.get_path("data_results")

    @property
    def log_file(self) -> Path:
        """Path to the modeling log file."""
        return PROJECT_ROOT / self._config["logging"]["log_file"]

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by dot-notation key.

        Args:
            key: Dot-notation key (e.g., 'modeling.fdr_threshold')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def save(self, path: Optional[Path] = None) -> None:
        """
        Save current configuration to a YAML file.

        Args:
            path: Optional path to save to. Defaults to config.yaml in project root.
        """
        save_path = path or self._config_path
        with open(save_path, "w", encoding="utf-8") as f:
            yaml.dump(self._config, f, default_flow_style=False, sort_keys=False)

    def __repr__(self) -> str:
        return f"Config(seed={self.random_seed}, root={PROJECT_ROOT})"


# Global configuration instance
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance.

    Returns:
        Global Config instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


def set_random_seed(seed: int) -> None:
    """
    Set the global random seed.

    Args:
        seed: Random seed value
    """
    get_config().set_random_seed(seed)


def get_data_path(key: str) -> Path:
    """
    Get a data path by key.

    Args:
        key: Path key (e.g., 'data_raw', 'data_processed')

    Returns:
        Absolute Path to the directory
    """
    return get_config().get_path(key)


if __name__ == "__main__":
    # Test configuration
    config = get_config()
    print(f"Project Root: {config.PROJECT_ROOT}")
    print(f"Random Seed: {config.random_seed}")
    print(f"Data Raw Dir: {config.data_raw_dir}")
    print(f"Data Processed Dir: {config.data_processed_dir}")
    print(f"Results Dir: {config.results_dir}")
    print(f"Log File: {config.log_file}")

    # Save config for verification
    config.save()
    print("Configuration saved successfully.")