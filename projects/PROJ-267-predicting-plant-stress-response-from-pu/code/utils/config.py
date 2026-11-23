"""
Project configuration module.

Defines common path constants and helper functions used throughout the
pipeline. All paths are resolved relative to the repository root
(the directory containing the top‑level ``code`` package).

This module provides the symbols expected by ``code.utils.__init__``:
``PROJECT_ROOT``, ``DATA_RAW_PATH``, ``DATA_PROCESSED_PATH``,
``LOG_PATH``, ``RESULTS_PATH``, ``LOG_LEVEL``, ``RANDOM_SEED``,
``SPECIES_LIST``, ``STRESS_LIST`` and ``REFERENCE_VALIDATOR_THRESHOLD``.

It also offers convenience getter functions that return ``Path`` objects.
"""

from pathlib import Path

# ----------------------------------------------------------------------
# Core paths
# ----------------------------------------------------------------------
# ``config.py`` lives in ``<project_root>/code/utils/``.
# The project root is therefore three levels up from this file.
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

def get_project_root() -> Path:
    """Return the absolute path to the project root directory."""
    return PROJECT_ROOT

def get_data_path() -> Path:
    """Return the absolute path to the ``data`` top‑level folder."""
    return PROJECT_ROOT / "data"

def get_results_path() -> Path:
    """Return the absolute path to the ``results`` top‑level folder."""
    return PROJECT_ROOT / "results"

def get_log_path() -> Path:
    """Return the absolute path to the ``logs`` top‑level folder."""
    return PROJECT_ROOT / "logs"

# Convenience sub‑folders (used by many modules)
DATA_RAW_PATH: Path = get_data_path() / "raw"
DATA_PROCESSED_PATH: Path = get_data_path() / "processed"
LOG_PATH: Path = get_log_path()
RESULTS_PATH: Path = get_results_path()

# ----------------------------------------------------------------------
# Miscellaneous constants
# ----------------------------------------------------------------------
LOG_LEVEL: str = "INFO"
RANDOM_SEED: int = 42

# Species and stress lists are referenced by several pipeline components.
SPECIES_LIST = ["Arabidopsis", "rice", "wheat"]
STRESS_LIST = ["Drought", "Salinity", "Heat"]

# Threshold used by the reference‑validation utilities.
REFERENCE_VALIDATOR_THRESHOLD: float = 0.8

# Exported names (optional, but keeps ``__all__`` tidy for linters)
__all__ = [
    "PROJECT_ROOT",
    "DATA_RAW_PATH",
    "DATA_PROCESSED_PATH",
    "LOG_PATH",
    "RESULTS_PATH",
    "LOG_LEVEL",
    "RANDOM_SEED",
    "SPECIES_LIST",
    "STRESS_LIST",
    "REFERENCE_VALIDATOR_THRESHOLD",
    "get_project_root",
    "get_data_path",
    "get_results_path",
    "get_log_path",
]
