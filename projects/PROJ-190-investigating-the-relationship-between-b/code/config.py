"""
Configuration module - Single Source of Truth for project settings.

This module defines all configurable parameters including random seeds,
file paths, and analysis thresholds.
"""
import os
from pathlib import Path
from typing import Final

# Project root directory
PROJECT_ROOT: Final[Path] = Path(__file__).parent.parent

# Data directories
DATA_RAW: Final[Path] = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED: Final[Path] = PROJECT_ROOT / "data" / "processed"
DATA_RESULTS: Final[Path] = PROJECT_ROOT / "data" / "results"

# State directory for checksums and pipeline state
STATE_DIR: Final[Path] = PROJECT_ROOT / "state" / "projects" / "PROJ-190-investigating-the-relationship-between-b"

# Random seed for reproducibility
RANDOM_SEED: Final[int] = 42

# Analysis thresholds
MAX_FRAMING_DISPLACEMENT: Final[float] = 0.5  # mm - subjects above this are excluded
MEAN_FD_WARNING_THRESHOLD: Final[float] = 0.2  # mm - warn if mean FD exceeds this
MIN_SUBJECT_RETENTION_RATIO: Final[float] = 0.5  # Minimum ratio of subjects to retain

# Graph analysis parameters
GRAPH_DENSITIES: Final[tuple] = (0.15, 0.20, 0.25)
RETAIN_POSITIVE_EDGES_ONLY: Final[bool] = True

# Statistical analysis parameters
PERMUTATION_WARMUP: Final[int] = 100
MAX_EXECUTION_TIME_HOURS: Final[float] = 6.0
MAX_EXECUTION_TIME_WARMUP_HOURS: Final[float] = 5.5
MIN_PERMUTATIONS: Final[int] = 1000
MAX_SUBJECTS_FOR_PERMUTATION: Final[int] = 500

# Atlas parameters
SCHAEFER_ROI_NODES: Final[int] = 100
SCHAEFER_MULTIPARCEL_NODES: Final[int] = 400

# VIF threshold
VIF_THRESHOLD: Final[float] = 5.0

def ensure_directories() -> None:
    """Create all required directories if they don't exist."""
    directories = [
        DATA_RAW,
        DATA_PROCESSED,
        DATA_RESULTS,
        STATE_DIR,
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def validate_config() -> bool:
    """Validate configuration settings."""
    # Check that all directories are valid paths
    if not PROJECT_ROOT.exists():
        raise ValueError(f"Project root does not exist: {PROJECT_ROOT}")

    # Validate thresholds
    if not 0 < MAX_FRAMING_DISPLACEMENT < 10:
        raise ValueError(f"Invalid MAX_FRAMING_DISPLACEMENT: {MAX_FRAMING_DISPLACEMENT}")

    if not 0 < MEAN_FD_WARNING_THRESHOLD < 10:
        raise ValueError(f"Invalid MEAN_FD_WARNING_THRESHOLD: {MEAN_FD_WARNING_THRESHOLD}")

    if not 0 < MIN_SUBJECT_RETENTION_RATIO <= 1:
        raise ValueError(f"Invalid MIN_SUBJECT_RETENTION_RATIO: {MIN_SUBJECT_RETENTION_RATIO}")

    # Validate graph densities
    for density in GRAPH_DENSITIES:
        if not 0 < density <= 1:
            raise ValueError(f"Invalid graph density: {density}")

    # Validate permutation parameters
    if PERMUTATION_WARMUP < 1:
        raise ValueError(f"Invalid PERMUTATION_WARMUP: {PERMUTATION_WARMUP}")

    if MAX_EXECUTION_TIME_HOURS <= 0:
        raise ValueError(f"Invalid MAX_EXECUTION_TIME_HOURS: {MAX_EXECUTION_TIME_HOURS}")

    if MIN_PERMUTATIONS < 1:
        raise ValueError(f"Invalid MIN_PERMUTATIONS: {MIN_PERMUTATIONS}")

    return True
