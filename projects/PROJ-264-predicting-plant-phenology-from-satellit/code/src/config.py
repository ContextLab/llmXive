"""
Configuration management for the plant phenology prediction pipeline.

This module adheres to the JSON Schema contract defined in
contracts/config_schema.json. It loads configuration from a YAML file
located at ``config/config.yaml`` (relative to the project root) and
validates it using ``jsonschema``. The configuration provides typed
access to required paths, seeds, and optional API keys.
"""

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from jsonschema import Draft7Validator, ValidationError

# ----------------------------------------------------------------------
# Resolve project‑root relative to this file.
# ``code/src/config.py`` → project root is three directories up.
# ----------------------------------------------------------------------
_CONFIG_FILE_PATH = Path(__file__).resolve()
_PROJECT_ROOT = _CONFIG_FILE_PATH.parent.parent.parent

# ----------------------------------------------------------------------
# Helper to load the JSON‑Schema contract.
# ----------------------------------------------------------------------
_SCHEMA_PATH = _PROJECT_ROOT / "contracts" / "config_schema.json"


def _load_schema() -> Dict[str, Any]:
    """Load the JSON‑Schema used to validate the configuration."""
    if not _SCHEMA_PATH.is_file():
        raise FileNotFoundError(f"Config schema not found at {_SCHEMA_PATH}")
    with open(_SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ----------------------------------------------------------------------
# Dataclass representing a validated configuration.
# ----------------------------------------------------------------------
@dataclass
class Config:
    # Required path fields (converted to absolute :class:`Path` objects)
    project_root: Path
    data_dir: Path
    raw_data_dir: Path
    processed_data_dir: Path
    artifacts_dir: Path
    models_dir: Path

    # Seed for reproducibility
    seed: int

    # Optional fields
    api_keys: Dict[str, str] = field(default_factory=dict)
    gee_credentials_path: Optional[Path] = None
    nature_notebook_api_key: Optional[str] = None

    def __post_init__(self) -> None:
        """Create any missing directories."""
        for p in (
            self.project_root,
            self.data_dir,
            self.raw_data_dir,
            self.processed_data_dir,
            self.artifacts_dir,
            self.models_dir,
        ):
            p.mkdir(parents=True, exist_ok=True)

    # Convenience accessors for environment‑based keys (kept for backward compatibility)
    @property
    def google_earth_engine_credentials(self) -> Optional[str]:
        """Return the GEE credentials string if present in ``api_keys``."""
        return self.api_keys.get("GOOGLE_EARTH_ENGINE")

    @property
    def natures_notebook_api_key(self) -> Optional[str]:
        """Return the Nature's Notebook API key if present."""
        return self.api_keys.get("NATURES_NOTEBOOK")

    @property
    def noaa_ghcn_api_key(self) -> Optional[str]:
        """Return the NOAA GHCN API key if present."""
        return self.api_keys.get("NOAA_GHCN")

    @property
    def nasa_power_api_key(self) -> Optional[str]:
        """Return the NASA POWER API key if present."""
        return self.api_keys.get("NASA_POWER")

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the configuration (excluding any secret values)."""
        return {
            "project_root": str(self.project_root),
            "data_dir": str(self.data_dir),
            "raw_data_dir": str(self.raw_data_dir),
            "processed_data_dir": str(self.processed_data_dir),
            "artifacts_dir": str(self.artifacts_dir),
            "models_dir": str(self.models_dir),
            "seed": self.seed,
            "api_keys": self.api_keys,
            "gee_credentials_path": (
                str(self.gee_credentials_path) if self.gee_credentials_path else None
            ),
            "nature_notebook_api_key": self.nature_notebook_api_key,
        }


# ----------------------------------------------------------------------
# Core loading logic
# ----------------------------------------------------------------------
def _load_yaml_config() -> Dict[str, Any]:
    """
    Load the YAML configuration file located at ``config/config.yaml``.
    The function raises ``FileNotFoundError`` if the file does not exist.
    """
    yaml_path = _PROJECT_ROOT / "config" / "config.yaml"
    if not yaml_path.is_file():
        raise FileNotFoundError(f"Configuration file not found at {yaml_path}")
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _validate_config(config_dict: Dict[str, Any]) -> None:
    """
    Validate ``config_dict`` against the JSON‑Schema contract.
    Raises ``jsonschema.ValidationError`` on the first validation error.
    """
    schema = _load_schema()
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(config_dict), key=lambda e: e.path)
    if errors:
        # Present the first error for brevity – the caller can catch the exception.
        raise ValidationError(errors[0].message)


def _build_config(validated: Dict[str, Any]) -> Config:
    """
    Convert a validated configuration dictionary into a :class:`Config` instance.
    Path strings are resolved relative to the project root.
    """
    # Helper to turn a possibly‑relative string into an absolute Path
    def _as_path(value: Optional[str]) -> Optional[Path]:
        if value is None:
            return None
        p = Path(value)
        return p if p.is_absolute() else (_PROJECT_ROOT / p)

    return Config(
        project_root=_as_path(validated.get("project_root")) or _PROJECT_ROOT,
        data_dir=_as_path(validated.get("data_dir")) or (_PROJECT_ROOT / "data"),
        raw_data_dir=_as_path(validated.get("raw_data_dir")) or (_PROJECT_ROOT / "data" / "raw"),
        processed_data_dir=_as_path(validated.get("processed_data_dir"))
        or (_PROJECT_ROOT / "data" / "processed"),
        artifacts_dir=_as_path(validated.get("artifacts_dir")) or (_PROJECT_ROOT / "artifacts"),
        models_dir=_as_path(validated.get("models_dir")) or (_PROJECT_ROOT / "artifacts" / "models"),
        seed=int(validated["seed"]),
        api_keys=validated.get("api_keys", {}),
        gee_credentials_path=_as_path(validated.get("gee_credentials_path")),
        nature_notebook_api_key=validated.get("nature_notebook_api_key"),
    )


def get_config() -> Config:
    """
    Load, validate and return the global configuration.
    The function aborts with a clear exception if the configuration file
    cannot be found or does not satisfy the schema.
    """
    raw_cfg = _load_yaml_config()
    _validate_config(raw_cfg)
    return _build_config(raw_cfg)


# ----------------------------------------------------------------------
# Singleton handling – convenient for the rest of the code base.
# ----------------------------------------------------------------------
_CONFIG_INSTANCE: Optional[Config] = None


def get_singleton_config() -> Config:
    """Return a cached ``Config`` instance, creating it on first use."""
    global _CONFIG_INSTANCE
    if _CONFIG_INSTANCE is None:
        _CONFIG_INSTANCE = get_config()
    return _CONFIG_INSTANCE


# Export a ready‑to‑use instance for simple imports.
config = get_singleton_config()

__all__ = [
    "Config",
    "get_config",
    "get_singleton_config",
    "config",
]
