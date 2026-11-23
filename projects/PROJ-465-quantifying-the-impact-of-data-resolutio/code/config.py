"""
Configuration management module for the gravitational wave resolution impact study.

This module handles environment variables, path resolution, and directory
initialization for the project's data and results artifacts.
"""
import os
from pathlib import Path
from typing import Optional


# Base project root (assumes code/ is a subdirectory of the root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data directories
DATA_DIR = _PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_DERIVED_DIR = DATA_DIR / "derived"

# Results directories
RESULTS_DIR = _PROJECT_ROOT / "results"
RESULTS_POSTERIORS_DIR = RESULTS_DIR / "posteriors"
RESULTS_METRICS_DIR = RESULTS_DIR / "metrics"

# Analysis outputs
ANALYSIS_DIR = RESULTS_DIR / "analysis"
VISUALIZATIONS_DIR = ANALYSIS_DIR / "visualizations"

# Cache directory for intermediate data
CACHE_DIR = _PROJECT_ROOT / ".cache"


def ensure_directories(base_dir: Optional[Path] = None) -> None:
    """
    Ensure that all required project directories exist.

    Creates the directory structure defined in the project plan if they
    do not already exist. This is idempotent.

    Args:
        base_dir: Optional base directory to start from. Defaults to
                  the project root derived from this module's location.
    """
    target_base = base_dir if base_dir is not None else _PROJECT_ROOT

    directories = [
        DATA_DIR,
        DATA_RAW_DIR,
        DATA_DERIVED_DIR,
        RESULTS_DIR,
        RESULTS_POSTERIORS_DIR,
        RESULTS_METRICS_DIR,
        ANALYSIS_DIR,
        VISUALIZATIONS_DIR,
        CACHE_DIR,
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
