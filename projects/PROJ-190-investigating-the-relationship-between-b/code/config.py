"""
Configuration module for the Brain Network Efficiency and Fluid Intelligence project.

This module serves as the Single Source of Truth for:
- Random seeds (for reproducibility)
- File paths (data directories, output locations)
- Processing thresholds (FD cutoffs, graph densities)
- Analysis parameters (permutation counts, time limits)
"""
import os
from pathlib import Path
from typing import Final

# --- Project Root & Directories ---
# Assume config.py is at code/config.py, so root is two levels up
_ROOT_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT: Final[Path] = _ROOT_DIR

# Standardized directory structure
DIR_RAW: Final[Path] = PROJECT_ROOT / "data" / "raw"
DIR_PROCESSED: Final[Path] = PROJECT_ROOT / "data" / "processed"
DIR_RESULTS: Final[Path] = PROJECT_ROOT / "data" / "results"
DIR_STATE: Final[Path] = PROJECT_ROOT / "state"
DIR_CODE: Final[Path] = PROJECT_ROOT / "code"
DIR_TESTS: Final[Path] = PROJECT_ROOT / "tests"
DIR_DOCS: Final[Path] = PROJECT_ROOT / "docs"

# --- Random Seeds ---
# Fixed seed for reproducibility across numpy, random, etc.
RANDOM_SEED: Final[int] = 42

# --- Data Quality Thresholds ---
# Framewise Displacement (FD) thresholds for subject exclusion and quality checks
FD_EXCLUSION_THRESHOLD: Final[float] = 0.5  # Exclude subjects with mean FD > 0.5 mm
FD_QUALITY_WARNING_THRESHOLD: Final[float] = 0.2  # Warn if mean FD of retained cohort > 0.2 mm

# --- Graph Analysis Parameters ---
# Target graph densities for thresholding (as per FR-009/SC-003)
GRAPH_DENSITIES: Final[list[float]] = [0.15, 0.20, 0.25]

# Atlas configuration
ATLAS_NAME: Final[str] = "Schaefer"
ATLAS_RESOLUTION: Final[int] = 100  # Default resolution (e.g., 100 parcels)

# --- Statistical Analysis Parameters ---
# Permutation testing settings
PERMUTATION_BASE_COUNT: Final[int] = 10000  # Default number of permutations
PERMUTATION_WARMUP_COUNT: Final[int] = 100  # Warm-up permutations to estimate time
MAX_ANALYSIS_TIME_HOURS: Final[float] = 6.0  # Hard time limit for analysis
WARMUP_TIME_THRESHOLD_HOURS: Final[float] = 5.5  # Switch to adaptive mode if elapsed > 5.5h

# Covariates for regression
COVARIATES: Final[list[str]] = ["age", "sex", "mean_fd"]

# --- Logging Configuration ---
LOG_LEVEL: Final[str] = "INFO"
LOG_FORMAT: Final[str] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# --- File Paths (Constants) ---
# Output paths for specific artifacts
PATH_REPORT: Final[Path] = DIR_RESULTS / "report.md"
PATH_CHECKSUMS: Final[Path] = DIR_STATE / "checksums.yaml"

# Ensure directories exist (lazy initialization helper)
def ensure_directories() -> None:
    """Create all required data and state directories if they don't exist."""
    for directory in [DIR_RAW, DIR_PROCESSED, DIR_RESULTS, DIR_STATE]:
        directory.mkdir(parents=True, exist_ok=True)

# --- Validation Helper ---
def validate_config() -> bool:
    """
    Validates that critical configuration values are within expected ranges.
    Returns True if valid, raises ValueError otherwise.
    """
    if not (0.0 < FD_EXCLUSION_THRESHOLD <= 1.0):
        raise ValueError(f"FD_EXCLUSION_THRESHOLD must be between 0 and 1, got {FD_EXCLUSION_THRESHOLD}")
    if not (0.0 < FD_QUALITY_WARNING_THRESHOLD <= 1.0):
        raise ValueError(f"FD_QUALITY_WARNING_THRESHOLD must be between 0 and 1, got {FD_QUALITY_WARNING_THRESHOLD}")
    if not all(0.0 < d <= 1.0 for d in GRAPH_DENSITIES):
        raise ValueError(f"GRAPH_DENSITIES must be between 0 and 1, got {GRAPH_DENSITIES}")
    if PERMUTATION_BASE_COUNT < 100:
        raise ValueError(f"PERMUTATION_BASE_COUNT must be at least 100, got {PERMUTATION_BASE_COUNT}")
    return True