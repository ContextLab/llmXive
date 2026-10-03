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

# Project Root
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent.parent

# Directory Paths
DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
DATA_RAW_DIR: Final[Path] = DATA_DIR / "raw"
DATA_PROCESSED_DIR: Final[Path] = DATA_DIR / "processed"
OUTPUT_DIR: Final[Path] = PROJECT_ROOT / "output"
OUTPUT_TEMPORAL_DIR: Final[Path] = OUTPUT_DIR / "temporal_profiles"
LOGS_DIR: Final[Path] = PROJECT_ROOT / "logs"
SPECS_DIR: Final[Path] = PROJECT_ROOT / "specs"
CONTRACTS_DIR: Final[Path] = PROJECT_ROOT / "contracts"

# MedDRA Mapping File Path
MEDDRA_MAPPING_PATH: Final[Path] = DATA_DIR / "meddra_soc_mapping.csv"

# Random Seed for reproducibility
RANDOM_SEED: Final[int] = 42

# Memory Limits (in GB)
MEMORY_LIMIT_CLEANING: Final[float] = 5.0
MEMORY_LIMIT_ANALYSIS: Final[float] = 7.0

# Metric Thresholds for Signal Detection (2-out-of-3 rule)
# These are internal thresholds used to flag signals based on the calculated
# disproportionality metrics from the dataset itself.
THRESHOLDS: Final[Dict[str, float]] = {
    "ror_min": 2.0,
    "ror_ci_min": 1.0,
    "prr_min": 1.5,
    "prr_ci_min": 1.0,
    "ic_min": 0.0,
    "ic_ci_min": 0.0
}

# Exit Codes
E_SUCCESS: Final[int] = 0
E_SCHEMA_MISSING: Final[int] = 1
E_MEMORY_LIMIT: Final[int] = 2
E_DATA_FETCH_FAILED: Final[int] = 3

def ensure_dirs() -> None:
    """Create all required directories if they do not exist."""
    directories = [
        DATA_DIR,
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        OUTPUT_DIR,
        OUTPUT_TEMPORAL_DIR,
        LOGS_DIR,
        CONTRACTS_DIR
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)