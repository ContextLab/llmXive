"""
utils/config.py
----------------
Configuration management for the glass-forming region prediction pipeline.

This module loads required environment variables, provides default values for
configurable thresholds, and validates that critical secrets are present.
It raises ``ConfigValidationError`` if validation fails.

Expected environment variables:
    - ``MATERIALS_PROJECT_API_KEY``: API key for the Materials Project API.
    - ``ZENO_DO_ID``: Identifier (DOI or record ID) for the Zenodo dataset.

Constants (with defaults) are also exposed:
    - ``LABEL_DROP_THRESHOLD`` (float, default 0.05)
    - ``CV_STABILITY_THRESHOLD`` (float, default 0.05)
    - ``MIN_DATASET_SIZE`` (int, default 1000)
"""

import os
import logging
from pathlib import Path
from typing import Final

logger = logging.getLogger(__name__)

class ConfigValidationError(RuntimeError):
    """Raised when required configuration values are missing or invalid."""
    pass


# ----------------------------------------------------------------------
# Helper functions to fetch and cast environment variables
# ----------------------------------------------------------------------
def _get_env_str(var_name: str) -> str:
    """Return a stripped string from ``os.getenv`` or raise if missing/empty."""
    value = os.getenv(var_name)
    if value is None or not value.strip():
        raise ConfigValidationError(f"Environment variable '{var_name}' is required and must be non‑empty.")
    return value.strip()


def _get_env_float(var_name: str, default: float) -> float:
    """Return a float from an env var or the provided default if not set."""
    raw = os.getenv(var_name)
    if raw is None or not raw.strip():
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ConfigValidationError(
            f"Environment variable '{var_name}' must be a valid float, got '{raw}'."
        ) from exc


def _get_env_int(var_name: str, default: int) -> int:
    """Return an int from an env var or the provided default if not set."""
    raw = os.getenv(var_name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigValidationError(
            f"Environment variable '{var_name}' must be a valid integer, got '{raw}'."
        ) from exc


# ----------------------------------------------------------------------
# Public accessor functions
# ----------------------------------------------------------------------
def get_materials_project_api_key() -> str:
    """Retrieve the Materials Project API key from the environment."""
    return _get_env_str("MATERIALS_PROJECT_API_KEY")


def get_zenodo_do_id() -> str:
    """Retrieve the Zenodo DOI/record identifier from the environment."""
    return _get_env_str("ZENO_DO_ID")


# ----------------------------------------------------------------------
# Configurable thresholds (constants with defaults)
# ----------------------------------------------------------------------
LABEL_DROP_THRESHOLD: Final[float] = _get_env_float("LABEL_DROP_THRESHOLD", 0.05)
CV_STABILITY_THRESHOLD: Final[float] = _get_env_float("CV_STABILITY_THRESHOLD", 0.05)
MIN_DATASET_SIZE: Final[int] = _get_env_int("MIN_DATASET_SIZE", 1000)


# ----------------------------------------------------------------------
# Validation entry point
# ----------------------------------------------------------------------
def validate_config() -> None:
    """
    Validate that all required configuration values are present.

    This function is idempotent; calling it multiple times is safe.
    It raises ``ConfigValidationError`` if any required variable is missing
    or empty.
    """
    # The helper functions raise on missing values.
    _ = get_materials_project_api_key()
    _ = get_zenodo_do_id()
    logger.debug(
        "Configuration validated: LABEL_DROP_THRESHOLD=%.3f, CV_STABILITY_THRESHOLD=%.3f, MIN_DATASET_SIZE=%d",
        LABEL_DROP_THRESHOLD,
        CV_STABILITY_THRESHOLD,
        MIN_DATASET_SIZE,
    )


# ----------------------------------------------------------------------
# Convenience: expose a dictionary of all config values (useful for debugging)
# ----------------------------------------------------------------------
def as_dict() -> dict:
    """Return a dictionary representation of the current configuration."""
    return {
        "MATERIALS_PROJECT_API_KEY": os.getenv("MATERIALS_PROJECT_API_KEY", "<missing>"),
        "ZENO_DO_ID": os.getenv("ZENO_DO_ID", "<missing>"),
        "LABEL_DROP_THRESHOLD": LABEL_DROP_THRESHOLD,
        "CV_STABILITY_THRESHOLD": CV_STABILITY_THRESHOLD,
        "MIN_DATASET_SIZE": MIN_DATASET_SIZE,
    }