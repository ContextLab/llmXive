"""
Configuration loader for the llmXive plant defense compound prediction pipeline.

Handles seeds, paths, hyperparameters, and verified URLs.
Loads from a YAML file located at `data/config.yaml` relative to the project root.
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, List, Union

# Define project root relative to this file (assuming code/config.py)
# Project structure: code/config.py, data/config.yaml
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_CONFIG_PATH = _PROJECT_ROOT / "data" / "config.yaml"

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

class Config:
    """
    Singleton-like configuration holder.
    Loads settings from a YAML file and provides typed access.
    """

    _instance: Optional['Config'] = None
    _data: Dict[str, Any]

    def __new__(cls, config_path: Optional[Path] = None) -> 'Config':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._data = {}
            cls._instance._load_config(config_path)
        return cls._instance

    def _load_config(self, config_path: Optional[Path]) -> None:
        """Load configuration from YAML file."""
        path = config_path or DEFAULT_CONFIG_PATH

        if not path.exists():
            # Create a default minimal config if it doesn't exist to allow execution
            # This prevents immediate failure during testing if config is missing
            self._generate_default_config(path)

        try:
            with open(path, 'r', encoding='utf-8') as f:
                self._data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ConfigError(f"Failed to parse configuration file: {e}")

    def _generate_default_config(self, path: Path) -> None:
        """Generate a default configuration file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        default_data = {
            "seeds": {
                "global_seed": 42,
                "train_test_split_seed": 123
            },
            "paths": {
                "raw_data_dir": "data/raw",
                "processed_data_dir": "data/processed",
                "figures_dir": "figures",
                "state_dir": "state",
                "schema_dir": "data/schema"
            },
            "hyperparameters": {
                "lasso_alpha": 0.1,
                "ridge_alpha": 1.0,
                "max_iter": 10000,
                "tol": 1e-4
            },
            "verified_urls": {
                "genomic": "https://ftp.ncbi.nlm.nih.gov/sra/",
                "env": "https://worldclim.org/data/",
                "compound": "https://chembank.broadinstitute.org/"
            },
            "thresholds": {
                "missingness_threshold": 0.20,
                "retention_threshold": 0.80,
                "vif_threshold": 5.0,
                "vif_instability_threshold": 10.0,
                "disk_space_buffer": 1.5
            }
        }
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(default_data, f, default_flow_style=False)

    @property
    def seeds(self) -> Dict[str, int]:
        """Get seed configuration."""
        return self._data.get("seeds", {})

    @property
    def paths(self) -> Dict[str, str]:
        """Get path configuration."""
        paths_config = self._data.get("paths", {})
        # Ensure paths are absolute relative to project root
        resolved = {}
        for key, val in paths_config.items():
            if val.startswith("data/") or val.startswith("figures/") or val.startswith("state/"):
                resolved[key] = str(_PROJECT_ROOT / val)
            else:
                resolved[key] = val
        return resolved

    @property
    def hyperparameters(self) -> Dict[str, Union[float, int]]:
        """Get hyperparameter configuration."""
        return self._data.get("hyperparameters", {})

    @property
    def verified_urls(self) -> Dict[str, str]:
        """Get verified URLs for data sources."""
        return self._data.get("verified_urls", {})

    @property
    def thresholds(self) -> Dict[str, float]:
        """Get processing thresholds."""
        return self._data.get("thresholds", {})

    def get(self, key: str, default: Any = None) -> Any:
        """Generic getter for nested keys using dot notation (e.g., 'seeds.global_seed')."""
        keys = key.split('.')
        value = self._data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    def __repr__(self) -> str:
        return f"Config(data={self._data})"


# Global instance for easy access
def get_config(config_path: Optional[Path] = None) -> Config:
    """Retrieve or create the global configuration instance."""
    return Config(config_path)


# Convenience function to load config immediately for scripts
config = get_config()