"""
Configuration module for the Brain Dynamics and Creativity pipeline.

This module defines the core configuration constants required by the
pipeline components, provides a singleton ``Config`` dataclass for
convenient access, and implements ``validate_fwe_config`` to ensure the
family‑wise error (FWE) correction method is valid.

The constants are also exposed at module level (e.g. ``WINDOW_SIZES``,
``STEP``, ``FWE_METHOD``) because several parts of the codebase import
them directly. They are initialised from environment variables when
available, otherwise they fall back to the defaults required by the
specification:

* ``WINDOW_SIZES`` – list of sliding‑window lengths in seconds,
  default ``[20, 30, 40]``.
* ``STEP`` – step size between windows in seconds, default ``5``.
* ``FWE_METHOD`` – family‑wise error correction method, default
  ``"max-t"`` (must be one of ``ALLOWED_FWE_METHODS``).

The ``Config`` dataclass mirrors these values and can be extended with
additional paths (e.g. ``ATLAS_PATH``, ``DATA_PATH``) that may be set via
environment variables.
"""

import os
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

# ----------------------------------------------------------------------
# Allowed family‑wise error correction methods
# ----------------------------------------------------------------------
ALLOWED_FWE_METHODS = {"max-t", "bonferroni"}

# ----------------------------------------------------------------------
# Helper to parse comma‑separated integer lists from environment vars
# ----------------------------------------------------------------------
def _parse_int_list(value: str) -> List[int]:
    """Parse a comma‑separated string of integers into a list."""
    return [int(item) for item in value.split(",") if item.strip()]

# ----------------------------------------------------------------------
# Module‑level configuration constants (used throughout the codebase)
# ----------------------------------------------------------------------
WINDOW_SIZES: List[int] = _parse_int_list(os.getenv("WINDOW_SIZES", "20,30,40"))
STEP: int = int(os.getenv("STEP", "5"))
ATLAS_PATH: Optional[str] = os.getenv("ATLAS_PATH")
# Default data root is the ``data`` directory at the project root.
DATA_PATH: Path = Path(os.getenv("DATA_PATH", "data"))
FWE_METHOD: str = os.getenv("FWE_METHOD", "max-t")

# ----------------------------------------------------------------------
# Helper functions for manifest handling and sample selection
# ----------------------------------------------------------------------
def _load_manifest_subject_ids() -> List[str]:
    """Load the list of subject IDs from the manifest file if it exists."""
    manifest_path = Path("data/raw/manifest.json")
    if manifest_path.is_file():
        try:
            with open(manifest_path, "r") as f:
                data = json.load(f)
                return data.get("subject_ids", [])
        except Exception:
            # If the manifest is malformed, fall back to empty list
            return []
    return []

def _select_sample_subject_ids(all_ids: List[str], sample_size: int = 1000) -> List[str]:
    """
    Deterministically select a sample of subject IDs.

    If fewer than ``sample_size`` IDs are available, all are returned.
    Otherwise a fixed‑seed random sample of ``sample_size`` IDs is chosen.
    """
    if len(all_ids) <= sample_size:
        return all_ids
    rng = random.Random(42)  # deterministic seed
    return rng.sample(all_ids, sample_size)

# ----------------------------------------------------------------------
# SAMPLE_SUBJECT_IDS constant (populated at import time)
# ----------------------------------------------------------------------
SAMPLE_SUBJECT_IDS: List[str] = _select_sample_subject_ids(_load_manifest_subject_ids())

# ----------------------------------------------------------------------
# Dataclass for a singleton configuration object
# ----------------------------------------------------------------------
@dataclass
class Config:
    """Container for configuration values with optional overrides."""
    WINDOW_SIZES: List[int] = None
    STEP: int = 5
    ATLAS_PATH: Optional[str] = None
    DATA_PATH: Optional[Path] = None
    FWE_METHOD: str = "max-t"

    def __post_init__(self):
        # Apply defaults if values were not supplied at construction time.
        if self.WINDOW_SIZES is None:
            self.WINDOW_SIZES = WINDOW_SIZES
        if self.ATLAS_PATH is None:
            self.ATLAS_PATH = ATLAS_PATH
        if self.DATA_PATH is None:
            self.DATA_PATH = DATA_PATH
        if self.FWE_METHOD is None:
            self.FWE_METHOD = FWE_METHOD

# ----------------------------------------------------------------------
# Singleton holder
# ----------------------------------------------------------------------
_config: Optional[Config] = None

def get_config() -> Config:
    """
    Return a singleton ``Config`` instance.

    Environment variables are read only once – the first call creates the
    ``Config`` object; subsequent calls return the same instance.
    """
    global _config
    if _config is None:
        _config = Config()
    return _config

# ----------------------------------------------------------------------
# Validation utilities
# ----------------------------------------------------------------------
def validate_fwe_config() -> None:
    """
    Validate the configured family‑wise error correction method.

    Raises
    ------
    ValueError
        If ``FWE_METHOD`` is not one of the allowed methods.
    """
    cfg = get_config()
    method = cfg.FWE_METHOD
    if method not in ALLOWED_FWE_METHODS:
        allowed = ", ".join(sorted(ALLOWED_FWE_METHODS))
        raise ValueError(
            f"Invalid FWE_METHOD '{method}'. Allowed values are: {allowed}."
        )