"""
Central configuration module.

Defines global constants (e.g., seed) and helper utilities for path handling.
"""

import os
from pathlib import Path
from typing import Final

# ----------------------------------------------------------------------
# Project root handling
# ----------------------------------------------------------------------
# This file lives at <project_root>/code/src/config.py.
# ``PROJECT_ROOT`` points to the top‑level directory of the repository
# (the directory that contains the ``code`` folder).
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]

# ----------------------------------------------------------------------
# Global reproducibility seed
# ----------------------------------------------------------------------
# The seed is used throughout the pipeline via ``src.lib.utils.set_global_seed``.
GLOBAL_SEED: Final[int] = 42

# ----------------------------------------------------------------------
# Data directory layout
# ----------------------------------------------------------------------
DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
STIMULI_RAW_DIR: Final[Path] = DATA_DIR / "stimuli" / "raw"
STIMULI_PROCESSED_DIR: Final[Path] = DATA_DIR / "stimuli" / "processed"
METRICS_DIR: Final[Path] = DATA_DIR / "processed"
MEASUREMENTS_DIR: Final[Path] = DATA_DIR / "measurements"
RAW_DIR: Final[Path] = DATA_DIR / "raw"
DERIVED_DIR: Final[Path] = DATA_DIR / "derived"

# Specific output files used by various modules
METRICS_CSV_PATH: Final[Path] = METRICS_DIR / "metrics.csv"

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def ensure_directories_exist() -> None:
    """
    Ensure that all required project directories exist.
    This is a convenience called by entry‑point scripts before they start
    processing data.
    """
    dirs = [
        DATA_DIR,
        STIMULI_RAW_DIR,
        STIMULI_PROCESSED_DIR,
        METRICS_DIR,
        MEASUREMENTS_DIR,
        RAW_DIR,
        DERIVED_DIR,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def get_relative_path(path: Path) -> Path:
    """
    Return ``path`` relative to ``PROJECT_ROOT``.
    Useful for logging or manifest generation.
    """
    return path.relative_to(PROJECT_ROOT)
