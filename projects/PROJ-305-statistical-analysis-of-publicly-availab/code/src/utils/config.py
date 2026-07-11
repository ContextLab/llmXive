"""
Configuration module for the COVID-19 Vaccine Adverse Event Analysis pipeline.

Defines paths, random seeds, metric thresholds, and known background rates
for statistical analysis.
"""
import os
from pathlib import Path
from typing import Dict, Final

# Project Root Configuration
# Assumes this file is at code/src/utils/config.py
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent.parent
DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
OUTPUT_DIR: Final[Path] = PROJECT_ROOT / "output"
SPEC_DIR: Final[Path] = PROJECT_ROOT / "specs"
CODE_DIR: Final[Path] = PROJECT_ROOT / "code"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Random Seed for reproducibility
RANDOM_SEED: Final[int] = 42

# Metric Thresholds for Signal Detection
# A signal is flagged if it meets the 2-out-of-3 rule:
# 1. ROR > 2.0 AND Lower CI > 1.0
# 2. PRR > 1.5 AND Lower CI > 1.0
# 3. IC > 0 AND Lower CI > 0
THRESHOLD_ROR: Final[float] = 2.0
THRESHOLD_PRR: Final[float] = 1.5
THRESHOLD_IC: Final[float] = 0.0

# Minimum report count per SOC to include in analysis
MIN_REPORT_COUNT: Final[int] = 5

# Memory Constraints (in GB)
MEMORY_LIMIT_CLEANING: Final[float] = 5.0
MEMORY_LIMIT_ANALYSIS: Final[float] = 7.0

# Known Background Rates
# Source: CDC literature and published incidence rates for specific System Organ Classes (SOCs).
# Mapping SOC codes (MedDRA High Level Group Terms or preferred SOC IDs) to incidence rates per 100,000 population.
# Note: These are approximations for the "Background Rate Unknown" flagging mechanism in T024b.
# If a SOC is not in this dictionary, it is flagged as having unknown background rate.
#
# SOC Codes used here correspond to standard MedDRA SOC IDs where possible,
# or simplified string keys matching the expected input from the cleaning pipeline.
#
# References:
# - CDC Vaccine Safety Datalink (VSD) background rates
# - Published epidemiological studies on adverse event incidence
KNOWN_BACKGROUND_RATES: Final[Dict[str, float]] = {
    # SOC: "Nervous system disorders" (ID: 10029205)
    "Nervous system disorders": 12.5,  # Example: General neurological events per 100k
    
    # SOC: "Cardiac disorders" (ID: 10007541)
    "Cardiac disorders": 8.2,  # Example: Myocarditis/Pericarditis baseline (varies by age)
    
    # SOC: "Respiratory, thoracic and mediastinal disorders" (ID: 10038738)
    "Respiratory, thoracic and mediastinal disorders": 45.0,
    
    # SOC: "Gastrointestinal disorders" (ID: 10017870)
    "Gastrointestinal disorders": 32.0,
    
    # SOC: "Skin and subcutaneous tissue disorders" (ID: 10040785)
    "Skin and subcutaneous tissue disorders": 28.5,
    
    # SOC: "Musculoskeletal and connective tissue disorders" (ID: 10028395)
    "Musculoskeletal and connective tissue disorders": 15.0,
    
    # SOC: "General disorders and administration site conditions" (ID: 10018065)
    "General disorders and administration site conditions": 150.0,  # High baseline for general reactions
    
    # SOC: "Infections and infestations" (ID: 10021881)
    "Infections and infestations": 55.0,
    
    # SOC: "Blood and lymphatic system disorders" (ID: 10005329)
    "Blood and lymphatic system disorders": 2.5,  # Rare events like thrombosis
    
    # SOC: "Renal and urinary disorders" (ID: 10037660)
    "Renal and urinary disorders": 5.0,
    
    # SOC: "Hepatobiliary disorders" (ID: 10019805)
    "Hepatobiliary disorders": 3.0,
    
    # SOC: "Metabolism and nutrition disorders" (ID: 10027433)
    "Metabolism and nutrition disorders": 10.0,
    
    # SOC: "Psychiatric disorders" (ID: 10037175)
    "Psychiatric disorders": 20.0,
    
    # SOC: "Vascular disorders" (ID: 10047065)
    "Vascular disorders": 4.0,
}

# File Paths for Data Artifacts
RAW_DATA_DIR: Final[Path] = DATA_DIR / "raw"
PROCESSED_DATA_DIR: Final[Path] = DATA_DIR / "processed"

# Ensure processed data directory exists
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Output File Paths
SIGNALS_OUTPUT: Final[Path] = OUTPUT_DIR / "signals.csv"
SENSITIVITY_OUTPUT: Final[Path] = OUTPUT_DIR / "sensitivity_analysis.csv"
TEMPORAL_PROFILES_DIR: Final[Path] = OUTPUT_DIR / "temporal_profiles"
REPORT_OUTPUT: Final[Path] = OUTPUT_DIR / "report.md"

# Ensure temporal profiles directory exists
TEMPORAL_PROFILES_DIR.mkdir(parents=True, exist_ok=True)

# Data Cleaning Output Paths
CLEANED_PARQUET: Final[Path] = PROCESSED_DATA_DIR / "cleaned_vaers.parquet"
CLEANED_CSV: Final[Path] = PROCESSED_DATA_DIR / "cleaned_vaers.csv"

# VAERS Source URLs (2020-2023)
# Using the official CDC VAERS data mirror
VAERS_BASE_URL: Final[str] = "https://vaers.hhs.gov/Data/VAERSDatasetsNew"
VAERS_YEARS: Final[list[int]] = [2020, 2021, 2022, 2023]

# Specific dataset names for download logic
# Format: {year}_DATA.zip
# Note: Actual download logic in download.py will construct the full URL
# Example: https://vaers.hhs.gov/Data/VAERSDatasetsNew/2020_DATA.zip
# This config just holds the base URL and years for reference.

# Logging Configuration
LOG_LEVEL: Final[str] = "INFO"
LOG_FORMAT: Final[str] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Statistical Constants
CONTINUITY_CORRECTION: Final[float] = 0.5
CONFIDENCE_LEVEL: Final[float] = 0.95
Z_SCORE_95: Final[float] = 1.96