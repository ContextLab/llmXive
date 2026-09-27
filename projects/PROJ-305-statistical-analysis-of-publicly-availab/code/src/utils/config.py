"""
Configuration module for the llmXive COVID-19 VAERS analysis pipeline.

This file defines internal analysis parameters, paths, and random seeds.
It does NOT load external background incidence rates. The analysis methodology
(ROR/PRR/IC) uses internal dataset counts as the denominator; external rates
are a known limitation and are not calculated.
"""

import os
from pathlib import Path
from typing import Dict, Final

# Project Root (assumed to be the directory containing 'code/')
# Adjust if running from a different context, but standard usage assumes
# this file is at code/src/utils/config.py
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Directory Paths
DATA_DIR: Final[Path] = _PROJECT_ROOT / "data"
RAW_DATA_DIR: Final[Path] = DATA_DIR / "raw"
PROCESSED_DATA_DIR: Final[Path] = DATA_DIR / "processed"
OUTPUT_DIR: Final[Path] = _PROJECT_ROOT / "output"
SIGNALS_DIR: Final[Path] = OUTPUT_DIR / "signals"
TEMPORAL_PROFILES_DIR: Final[Path] = OUTPUT_DIR / "temporal_profiles"
LOGS_DIR: Final[Path] = _PROJECT_ROOT / "logs"
CONTRACTS_DIR: Final[Path] = _PROJECT_ROOT / "contracts"
SPECS_DIR: Final[Path] = _PROJECT_ROOT / "specs"

# MedDRA Mapping File
MEDDRA_MAPPING_PATH: Final[Path] = DATA_DIR / "meddra_soc_mapping.csv"

# Random Seeds for reproducibility
RANDOM_SEED: Final[int] = 42

# Memory Constraints (in GB)
MEMORY_LIMIT_CLEANING: Final[float] = 5.0
MEMORY_LIMIT_ANALYSIS: Final[float] = 7.0

# Disproportionality Analysis Thresholds
# These are internal thresholds for the 2-out-of-3 rule.
# ROR: Reporting Odds Ratio
# PRR: Proportional Reporting Ratio
# IC: Information Component
# CI: Confidence Interval lower bound
THRESHOLDS: Final[Dict[str, float]] = {
    "ror_min": 2.0,
    "ror_ci_min": 1.0,
    "prr_min": 1.5,
    "prr_ci_min": 1.0,
    "ic_min": 0.0,
    "ic_ci_min": 0.0,
}

# Error Codes
E_SCHEMA_MISSING: Final[str] = "E_SCHEMA_MISSING"
E_MEMORY_LIMIT: Final[str] = "E_MEMORY_LIMIT"

def ensure_dirs() -> None:
    """Create all required directories if they do not exist."""
    dirs = [
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        OUTPUT_DIR,
        SIGNALS_DIR,
        TEMPORAL_PROFILES_DIR,
        LOGS_DIR,
        CONTRACTS_DIR,
        SPECS_DIR,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)