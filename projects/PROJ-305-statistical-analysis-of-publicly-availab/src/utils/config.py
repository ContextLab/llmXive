"""
Configuration module for the COVID-19 Vaccine Adverse Event Analysis pipeline.

This module defines internal analysis parameters, including paths, random seeds,
and metric thresholds for signal detection.

IMPORTANT: This file defines internal analysis parameters only. It does NOT load
external background incidence rates. The analysis methodology (ROR/PRR/IC) uses
internal dataset counts as the denominator; external rates are a known limitation
and are not calculated.
"""

import os
from pathlib import Path
from typing import Dict, Final

# ----------------------------------------------------------------------
# Project paths
# ----------------------------------------------------------------------
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent.parent

DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
DATA_RAW_DIR: Final[Path] = DATA_DIR / "raw"
DATA_PROCESSED_DIR: Final[Path] = DATA_DIR / "processed"
OUTPUT_DIR: Final[Path] = PROJECT_ROOT / "output"
OUTPUT_TEMPORAL_DIR: Final[Path] = OUTPUT_DIR / "temporal_profiles"
LOGS_DIR: Final[Path] = PROJECT_ROOT / "logs"
CODE_DIR: Final[Path] = PROJECT_ROOT / "code"
CONTRACTS_DIR: Final[Path] = PROJECT_ROOT / "contracts"


# ----------------------------------------------------------------------
# Directory creation helper
# ----------------------------------------------------------------------
def ensure_dirs() -> None:
    """Create all required directories if they do not exist."""
    directories = [
        DATA_DIR,
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        OUTPUT_DIR,
        OUTPUT_TEMPORAL_DIR,
        LOGS_DIR,
        CONTRACTS_DIR,
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


# ----------------------------------------------------------------------
# Random seed for reproducibility
# ----------------------------------------------------------------------
RANDOM_SEED: Final[int] = 42

# ----------------------------------------------------------------------
# Memory limits (in GB)
# ----------------------------------------------------------------------
MEMORY_LIMIT_CLEANING: Final[float] = 5.0
MEMORY_LIMIT_ANALYSIS: Final[float] = 7.0

# ----------------------------------------------------------------------
# Metric thresholds (2‑out‑of‑3 rule)
# ----------------------------------------------------------------------
THRESHOLDS: Final[Dict[str, float]] = {
    "ror_min": 2.0,
    "ror_ci_min": 1.0,
    "prr_min": 1.5,
    "prr_ci_min": 1.0,
    "ic_min": 0.0,
    "ic_ci_min": 0.0,
}

# ----------------------------------------------------------------------
# Exported names required by task T005
# ----------------------------------------------------------------------
# Seed alias expected by tests
SEED: Final[int] = RANDOM_SEED

# Path constants expected by downstream code and tests
RAW_DIR: Final[Path] = DATA_RAW_DIR
PROCESSED_DIR: Final[Path] = DATA_PROCESSED_DIR
# OUTPUT_DIR and CONTRACTS_DIR are already defined with the exact names required

# Individual metric threshold constants required by tests / scripts
ROR_THRESH: Final[float] = 2.0
PRR_THRESH: Final[float] = 1.5
IC_THRESH: Final[float] = 0.0
BH_ALPHA: Final[float] = 0.05

# ----------------------------------------------------------------------
# End of configuration module
# ----------------------------------------------------------------------
