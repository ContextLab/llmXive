"""
Configuration management for the plant phenology prediction pipeline.

This module adheres to the JSON Schema contract defined in
contracts/config_schema.json. It provides typed access to paths, seeds,
and API keys without hardcoding secrets.
"""

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# Project root is two levels up from this file (code/src/config.py -> code/ -> root)
# However, based on task T001a/T001b structure in tasks.md, the root is likely
# where 'code/', 'data/', 'tests/' live.
# Assuming this file is at code/src/config.py, the project root is code/../
# Let's dynamically determine the project root relative to the config file.
_CONFIG_FILE_PATH = Path(__file__).resolve()
# Assuming structure: <root>/code/src/config.py
# Root = <root>/
_PROJECT_ROOT = _CONFIG_FILE_PATH.parent.parent.parent

# Default paths relative to project root
DEFAULT_DATA_DIR = _PROJECT_ROOT / "data"
DEFAULT_DATA_RAW_DIR = DEFAULT_DATA_DIR / "raw"
DEFAULT_DATA_PROCESSED_DIR = DEFAULT_DATA_DIR / "processed"
DEFAULT_ARTIFACTS_DIR = _PROJECT_ROOT / "artifacts"
DEFAULT_MODELS_DIR = DEFAULT_ARTIFACTS_DIR / "models"
DEFAULT_FIGURES_DIR = _PROJECT_ROOT / "figures"
DEFAULT_LOGS_DIR = _PROJECT_ROOT / "logs"
DEFAULT_SPECS_DIR = _PROJECT_ROOT / "specs"
DEFAULT_CONTRACTS_DIR = _PROJECT_ROOT / "contracts"

# Default seed for reproducibility
DEFAULT_SEED = 42


@dataclass
class Config:
    """
    Configuration container for the phenology prediction pipeline.

    Attributes match the schema in contracts/config_schema.json:
    - paths: Directory paths for data, artifacts, logs, etc.
    - seeds: Random seeds for reproducibility.
    - api_keys: Dictionary for external API keys (loaded from env vars).
    """

    # --- Paths ---
    data_dir: Path = field(default_factory=lambda: DEFAULT_DATA_DIR)
    data_raw_dir: Path = field(default_factory=lambda: DEFAULT_DATA_RAW_DIR)
    data_processed_dir: Path = field(default_factory=lambda: DEFAULT_DATA_PROCESSED_DIR)
    artifacts_dir: Path = field(default_factory=lambda: DEFAULT_ARTIFACTS_DIR)
    models_dir: Path = field(default_factory=lambda: DEFAULT_MODELS_DIR)
    figures_dir: Path = field(default_factory=lambda: DEFAULT_FIGURES_DIR)
    logs_dir: Path = field(default_factory=lambda: DEFAULT_LOGS_DIR)
    specs_dir: Path = field(default_factory=lambda: DEFAULT_SPECS_DIR)
    contracts_dir: Path = field(default_factory=lambda: DEFAULT_CONTRACTS_DIR)

    # --- Seeds ---
    seed: int = DEFAULT_SEED
    random_state: int = DEFAULT_SEED

    # --- API Keys (loaded from environment variables) ---
    # We do not store raw secrets in the dataclass instance to avoid accidental logging,
    # but we provide accessors. The values here are placeholders if env vars are missing.
    # Actual values are loaded in `__post_init__` or via properties.
    _env_api_keys: Dict[str, str] = field(default_factory=dict, repr=False, compare=False)

    # Specific API Key Names expected in environment
    API_KEY_NAMES: Dict[str, str] = field(default_factory=lambda: {
        "GOOGLE_EARTH_ENGINE": "GOOGLE_EARTH_ENGINE_CREDENTIALS",
        "NATURES_NOTEBOOK": "NATURES_NOTEBOOK_API_KEY",
        "NOAA_GHCN": "NOAA_GHCN_API_KEY",
        "NASA_POWER": "NASA_POWER_API_KEY"
    })

    def __post_init__(self):
        """Load API keys from environment variables after initialization."""
        self._load_api_keys()
        self._ensure_directories_exist()

    def _load_api_keys(self) -> None:
        """
        Load API keys from environment variables.
        If an env var is missing, the key is not added to the internal dict,
        or a warning can be raised if strict mode is enabled.
        """
        for key_name, env_var in self.API_KEY_NAMES.items():
            value = os.getenv(env_var)
            if value:
                self._env_api_keys[key_name] = value
            else:
                # We allow missing keys if the code handles them gracefully later,
                # but for T004 we just ensure the structure is ready.
                pass

    def _ensure_directories_exist(self) -> None:
        """Create all configured directories if they do not exist."""
        dirs_to_create: List[Path] = [
            self.data_dir,
            self.data_raw_dir,
            self.data_processed_dir,
            self.artifacts_dir,
            self.models_dir,
            self.figures_dir,
            self.logs_dir,
            self.specs_dir,
            self.contracts_dir,
        ]
        for d in dirs_to_create:
            d.mkdir(parents=True, exist_ok=True)

    @property
    def google_earth_engine_credentials(self) -> Optional[str]:
        """Returns the GEE credentials string or None."""
        return self._env_api_keys.get("GOOGLE_EARTH_ENGINE")

    @property
    def natures_notebook_api_key(self) -> Optional[str]:
        """Returns the Nature's Notebook API key or None."""
        return self._env_api_keys.get("NATURES_NOTEBOOK")

    @property
    def noaa_ghcn_api_key(self) -> Optional[str]:
        """Returns the NOAA GHCN API key or None."""
        return self._env_api_keys.get("NOAA_GHCN")

    @property
    def nasa_power_api_key(self) -> Optional[str]:
        """Returns the NASA POWER API key or None."""
        return self._env_api_keys.get("NASA_POWER")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to a dictionary for serialization.
        Excludes API keys to prevent accidental leakage.
        """
        return {
            "paths": {
                "data_dir": str(self.data_dir),
                "data_raw_dir": str(self.data_raw_dir),
                "data_processed_dir": str(self.data_processed_dir),
                "artifacts_dir": str(self.artifacts_dir),
                "models_dir": str(self.models_dir),
                "figures_dir": str(self.figures_dir),
                "logs_dir": str(self.logs_dir),
                "specs_dir": str(self.specs_dir),
                "contracts_dir": str(self.contracts_dir),
            },
            "seeds": {
                "seed": self.seed,
                "random_state": self.random_state,
            },
            "api_keys": {
                k: "SET" if v else "MISSING"
                for k, v in self.API_KEY_NAMES.items()
            }
        }

    @classmethod
    def from_json(cls, path: Path) -> "Config":
        """
        Load configuration from a JSON file.
        Note: API keys are NOT loaded from the JSON file for security reasons.
        They must be set via environment variables.
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Map JSON keys to dataclass fields
        # This assumes the JSON structure matches the dataclass fields roughly
        # or provides a subset.
        config_kwargs = {}

        # Handle paths
        if "paths" in data:
            for key, value in data["paths"].items():
                if hasattr(cls, key) and isinstance(value, str):
                    config_kwargs[key] = Path(value)

        # Handle seeds
        if "seeds" in data:
            for key, value in data["seeds"].items():
                if hasattr(cls, key):
                    config_kwargs[key] = value

        return cls(**config_kwargs)

    def validate(self) -> List[str]:
        """
        Validate the configuration against the schema contract.
        Returns a list of error messages. Empty list if valid.
        """
        errors = []

        # Check required paths exist (they should be created by __post_init__ but verify)
        required_paths = [
            self.data_dir, self.data_raw_dir, self.data_processed_dir,
            self.artifacts_dir, self.models_dir, self.figures_dir, self.logs_dir
        ]
        for p in required_paths:
            if not p.exists():
                errors.append(f"Path does not exist: {p}")

        # Check seeds are integers
        if not isinstance(self.seed, int):
            errors.append("Seed must be an integer")
        if not isinstance(self.random_state, int):
            errors.append("Random state must be an integer")

        # Check API keys (optional for validation if not needed, but good to warn)
        # For strict validation, we might require GEE key if GEE tasks are planned.
        # For T004, we just ensure the structure is there.

        return errors


def get_config() -> Config:
    """
    Factory function to get the global configuration instance.
    Checks for a config.json file in the project root or contracts directory.
    Falls back to defaults if no file is found.
    """
    possible_paths = [
        _PROJECT_ROOT / "config.json",
        _PROJECT_ROOT / "data" / "config.json",
        _PROJECT_ROOT / "contracts" / "config.json",
    ]

    for p in possible_paths:
        if p.exists():
            try:
                return Config.from_json(p)
            except Exception as e:
                print(f"Warning: Failed to load config from {p}: {e}. Using defaults.", file=sys.stderr)
                break

    return Config()


# Singleton instance for easy import
_CONFIG_INSTANCE: Optional[Config] = None

def get_singleton_config() -> Config:
    global _CONFIG_INSTANCE
    if _CONFIG_INSTANCE is None:
        _CONFIG_INSTANCE = get_config()
    return _CONFIG_INSTANCE

# Convenience exports
config = get_singleton_config()

# Ensure this module can be imported as `from src.config import config`
# or `from src.config import Config, get_config`
__all__ = ["Config", "get_config", "get_singleton_config", "config", "DEFAULT_SEED"]
