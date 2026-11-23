"""
Configuration management for seeds, paths, and data sources.
Implements T004 requirements.
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

# Project Root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Default paths based on T001a/b/c
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_CODE_DIR = PROJECT_ROOT / "code"
DEFAULT_TESTS_DIR = PROJECT_ROOT / "tests"
DEFAULT_FINAL_DIR = DEFAULT_DATA_DIR / "final"
DEFAULT_PROCESSED_DIR = DEFAULT_DATA_DIR / "processed"
DEFAULT_RAW_DIR = DEFAULT_DATA_DIR / "raw"

# Configuration Keys
SEED_KEY = "random_seed"
DEFAULT_SEED = 42
EXCLUSION_RATE_KEY = "max_exclusion_rate"
DEFAULT_EXCLUSION_RATE = 0.05
CLOUD_THRESHOLD_KEY = "cloud_threshold"
DEFAULT_CLOUD_THRESHOLD = 0.10  # 10% cloud cover max

class Config:
    """
    Centralized configuration handler.
    Loads from environment variables or a config.yaml file if present.
    Falls back to defaults.
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or (PROJECT_ROOT / "config.yaml")
        self._config: Dict[str, Any] = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load config from file or return defaults."""
        base_config = {
            "paths": {
                "data": str(DEFAULT_DATA_DIR),
                "raw": str(DEFAULT_RAW_DIR),
                "processed": str(DEFAULT_PROCESSED_DIR),
                "final": str(DEFAULT_FINAL_DIR),
                "code": str(DEFAULT_CODE_DIR),
                "tests": str(DEFAULT_TESTS_DIR),
            },
            "hyperparams": {
                "random_seed": DEFAULT_SEED,
                "max_exclusion_rate": DEFAULT_EXCLUSION_RATE,
                "cloud_threshold": DEFAULT_CLOUD_THRESHOLD,
            },
            "data_sources": {
                "hybiomass_url": "https://hybiomass.org/data", # Placeholder, updated in T010
                "neon_url": "https://data.neonscience.org",   # Placeholder, updated in T010
            }
        }

        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    file_config = yaml.safe_load(f) or {}
                    # Deep merge logic could be added here, but simple override for now
                    base_config.update(file_config)
            except Exception as e:
                raise RuntimeError(f"Failed to load config from {self.config_path}: {e}")

        return base_config

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a configuration value."""
        parts = key.split(".")
        val = self._config
        for part in parts:
            if isinstance(val, dict) and part in val:
                val = val[part]
            else:
                return default
        return val

    @property
    def data_dir(self) -> Path:
        return Path(self.get("paths.data"))

    @property
    def raw_dir(self) -> Path:
        return Path(self.get("paths.raw"))

    @property
    def processed_dir(self) -> Path:
        return Path(self.get("paths.processed"))

    @property
    def final_dir(self) -> Path:
        return Path(self.get("paths.final"))

    @property
    def random_seed(self) -> int:
        return self.get("hyperparams.random_seed", DEFAULT_SEED)

    @property
    def max_exclusion_rate(self) -> float:
        return self.get("hyperparams.max_exclusion_rate", DEFAULT_EXCLUSION_RATE)

    @property
    def cloud_threshold(self) -> float:
        return self.get("hyperparams.cloud_threshold", DEFAULT_CLOUD_THRESHOLD)

    def ensure_directories(self) -> None:
        """Create all required data directories if they don't exist."""
        for dir_path in [self.data_dir, self.raw_dir, self.processed_dir, self.final_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def __repr__(self) -> str:
        return f"Config(seed={self.random_seed}, data_dir={self.data_dir})"


# Singleton instance for global access
_config_instance: Optional[Config] = None

def get_config() -> Config:
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
