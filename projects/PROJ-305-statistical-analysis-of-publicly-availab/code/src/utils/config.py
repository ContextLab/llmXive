"""
Configuration module for the COVID-19 Vaccine Adverse Event Analysis pipeline.
Defines paths, random seeds, metric thresholds, and known background rates.
"""
import os
from pathlib import Path
from typing import Dict, Final

# Project Root
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent.parent

# Directory Paths
DATA_RAW_DIR: Final[Path] = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR: Final[Path] = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR: Final[Path] = PROJECT_ROOT / "output"
OUTPUT_TEMPORAL_DIR: Final[Path] = OUTPUT_DIR / "temporal_profiles"
SPECS_DIR: Final[Path] = PROJECT_ROOT / "specs"
CONTRACTS_DIR: Final[Path] = PROJECT_ROOT / "contracts"

# Random Seeds
RANDOM_SEED: Final[int] = 42

# Metric Thresholds for Signal Detection (2-out-of-3 rule components)
# A signal is flagged if at least 2 of these conditions are met:
# 1. ROR > 2.0 AND Lower CI > 1.0
# 2. PRR > 1.5 AND Lower CI > 1.0
# 3. IC > 0 AND Lower CI > 0
THRESHOLD_ROR: Final[float] = 2.0
THRESHOLD_PRR: Final[float] = 1.5
THRESHOLD_IC: Final[float] = 0.0
THRESHOLD_CI_LOWER: Final[float] = 1.0  # For ROR/PRR (must be > 1)
THRESHOLD_IC_CI_LOWER: Final[float] = 0.0  # For IC (must be > 0)

# Minimum report count per SOC to include in analysis
MIN_REPORT_COUNT: Final[int] = 5

# Memory Limits (GB)
MEMORY_LIMIT_CLEANING: Final[float] = 5.0
MEMORY_LIMIT_ANALYSIS: Final[float] = 7.0

# Known Background Rates (Incidence per 1,000,000 population)
# Source: CDC literature and general epidemiological estimates for US population.
# Mapping: SOC Code (String) -> Incidence Rate (float)
# Note: These are approximate background rates used for context in T024b.
# SOCs not listed here will be flagged as "Background Rate Unknown".
KNOWN_BACKGROUND_RATES: Final[Dict[str, float]] = {
    # Cardiac disorders
    "10007541": 450.0,  # Cardiac disorders (General estimate)
    # Gastrointestinal disorders
    "10017471": 1200.0, # Gastrointestinal disorders
    # Nervous system disorders
    "10029239": 850.0,  # Nervous system disorders
    # Respiratory, thoracic and mediastinal disorders
    "10038733": 600.0,  # Respiratory disorders
    # Skin and subcutaneous tissue disorders
    "10040785": 950.0,  # Skin disorders
    # Vascular disorders
    "10047065": 350.0,  # Vascular disorders (e.g., thrombosis)
    # Immune system disorders
    "10021409": 200.0,  # Immune system disorders
    # Infections and infestations
    "10021861": 2500.0, # Infections
    # Musculoskeletal and connective tissue disorders
    "10028395": 700.0,  # Musculoskeletal disorders
    # General disorders and administration site conditions
    "10018065": 1500.0, # General disorders (e.g., fatigue, fever)
}

def ensure_dirs() -> None:
    """Create all required directories if they do not exist."""
    directories = [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        OUTPUT_DIR,
        OUTPUT_TEMPORAL_DIR,
        SPECS_DIR,
        CONTRACTS_DIR,
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)