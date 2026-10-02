"""
Configuration module for the project.

This module defines global constants such as the random seed, project root,
and standard data directories. It also provides a helper to ensure that all
required directories exist before the pipeline runs.
"""

import os
from pathlib import Path
from typing import Final, List

# ----------------------------------------------------------------------
# Global random seed
# ----------------------------------------------------------------------
# The seed is used throughout the project to guarantee reproducibility.
# It is deliberately defined as a constant so that tests can import it
# directly (see ``tests/test_config.py``).
GLOBAL_SEED: Final[int] = 42

# ----------------------------------------------------------------------
# Project root and data directory definitions
# ----------------------------------------------------------------------
# ``__file__`` points to ``<repo_root>/code/src/config.py``.
# The repository root is therefore three parents up from this file:
#   config.py -> src -> code -> <repo_root>
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[3]

# Standardised data directories used by the pipeline.
DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
STIMULI_RAW_DIR: Final[Path] = DATA_DIR / "stimuli" / "raw"
STIMULI_PROCESSED_DIR: Final[Path] = DATA_DIR / "stimuli" / "processed"
METRICS_DIR: Final[Path] = DATA_DIR / "processed"
MEASUREMENTS_DIR: Final[Path] = DATA_DIR / "measurements"
RAW_MEASUREMENTS_DIR: Final[Path] = MEASUREMENTS_DIR / "raw"
DERIVED_DIR: Final[Path] = DATA_DIR / "derived"

# Path to the metrics CSV file produced by ``src.metrics.extract``.
METRICS_CSV_PATH: Final[Path] = METRICS_DIR / "metrics.csv"

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _ensure_dir(path: Path) -> None:
    """
    Ensure that a single directory exists.

    Parameters
    ----------
    path: Path
        The directory to create (parents are created as needed).
    """
    path.mkdir(parents=True, exist_ok=True)

def ensure_directories_exist() -> List[Path]:
    """
    Create all required project directories.

    Returns
    -------
    List[Path]
        A list of directories that were ensured to exist.
    """
    required_dirs = [
        # Source code package directories
        PROJECT_ROOT / "src" / "lib",
        PROJECT_ROOT / "src" / "metrics",
        PROJECT_ROOT / "src" / "experiment",
        PROJECT_ROOT / "src" / "analysis",
        # Test directory
        PROJECT_ROOT / "tests",
        # Data directories
        DATA_DIR,
        DATA_DIR / "stimuli",
        STIMULI_RAW_DIR,
        STIMULI_PROCESSED_DIR,
        METRICS_DIR,
        MEASUREMENTS_DIR,
        RAW_MEASUREMENTS_DIR,
        DERIVED_DIR,
    ]

    for d in required_dirs:
        _ensure_dir(d)

    return required_dirs

def get_relative_path(*parts: str) -> Path:
    """
    Construct a path relative to the project root.

    This utility mirrors the function that already existed in the original
    ``src/config.py`` (kept for backward compatibility).

    Parameters
    ----------
    *parts: str
        Path components to join.

    Returns
    -------
    Path
        The absolute path obtained by joining ``PROJECT_ROOT`` with the
        supplied parts.
    """
    return PROJECT_ROOT.joinpath(*parts)