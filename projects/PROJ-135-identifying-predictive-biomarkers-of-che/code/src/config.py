"""
Configuration module for the Chemo Biomarker Discovery project.

Defines paths, random seeds, FDR thresholds, CPU/memory limits, and constants.
"""

import os
from pathlib import Path
from typing import Final

# Project Root
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent

# Directories
DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
RAW_DIR: Final[Path] = DATA_DIR / "raw"
PROCESSED_DIR: Final[Path] = DATA_DIR / "processed"
RESULTS_DIR: Final[Path] = PROJECT_ROOT / "results"
META_ANALYSIS_DIR: Final[Path] = RESULTS_DIR / "meta_analysis"
TESTS_DIR: Final[Path] = PROJECT_ROOT / "tests"
SPECS_DIR: Final[Path] = PROJECT_ROOT / "specs" / "001-chemo-biomarker-discovery"
STATE_DIR: Final[Path] = PROJECT_ROOT / "state"

# Random Seeds
RANDOM_SEED: Final[int] = 42

# Statistical Thresholds
FDR_THRESHOLD: Final[float] = 0.05
LOG2FC_THRESHOLD: Final[float] = 1.0

# Resource Limits
MAX_VARIANCE_GENES: Final[int] = 10000
MAX_MEMORY_MB: Final[int] = 8192  # 8 GB
TIMEOUT_HOURS: Final[int] = 5

# Data Acquisition
MIN_TUMOR_TYPES: Final[int] = 3
MIN_SAMPLES_PER_TYPE: Final[int] = 100

def ensure_directories():
    """Create all required directories if they don't exist."""
    dirs = [
        DATA_DIR, RAW_DIR, PROCESSED_DIR, RESULTS_DIR,
        META_ANALYSIS_DIR, TESTS_DIR, SPECS_DIR, STATE_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
