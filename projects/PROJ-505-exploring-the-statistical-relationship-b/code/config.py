"""
Configuration module: random seed and canonical data-path constants.
Provides both a get_config() helper and module-level constants for easy import.
"""

import os
from pathlib import Path
from typing import Final, Dict, Any

# ----------------------------------------------------------------------
# Core constants
# ----------------------------------------------------------------------
# Random seed for reproducibility across the project
SEED: Final[int] = 42

# Base directories – resolved relative to the project root (two levels up from this file)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Directory where raw data files are stored (unchanged source files)
RAW_DIR: Final[Path] = _PROJECT_ROOT / "data" / "raw"

# Directory for processed, aligned datasets
PROC_DIR: Final[Path] = _PROJECT_ROOT / "data" / "processed"

# Directory for generated artefacts (models, reports, etc.)
ARTIFACT_DIR: Final[Path] = _PROJECT_ROOT / "data" / "artifacts"

# ----------------------------------------------------------------------
# Helper to return a configuration dictionary (kept for backward compatibility)
# ----------------------------------------------------------------------
def get_config() -> Dict[str, Any]:
    """
    Return a dictionary with project‑wide configuration values.

    This function mirrors the original API used throughout the codebase,
    while the module‑level constants above provide a more convenient import
    style for new code (e.g. ``from config import SEED, RAW_DIR``).
    """
    return {
        "seed": SEED,
        "start_date": "2000-01-01",
        "end_date": "2023-12-31",
        "data_dir": Path("data"),
        "code_dir": Path("code"),
        "output_dir": Path("data/artifacts")
    }