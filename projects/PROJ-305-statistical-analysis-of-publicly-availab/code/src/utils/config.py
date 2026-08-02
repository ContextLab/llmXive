"""
Configuration module for the VAERS Statistical Analysis pipeline.
Defines paths, random seeds, metric thresholds, and known background rates.
"""
import os
from pathlib import Path
from typing import Dict, Final

# Project Root
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[3]

# Directory Paths
DATA_RAW_DIR: Final[Path] = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR: Final[Path] = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR: Final[Path] = PROJECT_ROOT / "output"
OUTPUT_TEMPORAL_DIR: Final[Path] = OUTPUT_DIR / "temporal_profiles"
CONTRACTS_DIR: Final[Path] = PROJECT_ROOT / "contracts"

# Ensure directories exist (lazy initialization pattern)
def ensure_dirs() -> None:
    """Create all required data and output directories if they don't exist."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_TEMPORAL_DIR.mkdir(parents=True, exist_ok=True)
    CONTRACTS_DIR.mkdir(parents=True, exist_ok=True)

# Random Seeds for reproducibility
RANDOM_SEED: Final[int] = 42

# Metric Thresholds for Signal Detection (2-out-of-3 rule)
# ROR > 2.0 and lower CI > 1.0
ROR_THRESHOLD: Final[float] = 2.0
ROR_CI_LOWER_THRESHOLD: Final[float] = 1.0

# PRR > 1.5 and lower CI > 1.0
PRR_THRESHOLD: Final[float] = 1.5
PRR_CI_LOWER_THRESHOLD: Final[float] = 1.0

# IC > 0 and lower CI > 0
IC_THRESHOLD: Final[float] = 0.0
IC_CI_LOWER_THRESHOLD: Final[float] = 0.0

# Minimum report count for a SOC to be included in analysis
MIN_REPORTS_THRESHOLD: Final[int] = 5

# Memory thresholds (GB)
MEMORY_CLEAN_THRESHOLD_GB: Final[float] = 5.0
MEMORY_ANALYSIS_THRESHOLD_GB: Final[float] = 7.0

# Known Background Rates (incidence per 100,000 population)
# Source: CDC literature, FDA/CBER background rate tables, and published epidemiological studies.
# These are approximate annual incidence rates used for context in T024b.
# Format: SOC_CODE -> Rate per 100,000
# Note: These are static approximations. Real-time rates vary by age, geography, and year.
KNOWN_BACKGROUND_RATES: Final[Dict[str, float]] = {
    # System Organ Classes (SOC) mapped to approximate incidence rates
    # Based on CDC/WHO data for general population (annualized)
    "10000000": 125.0,   # Infections and infestations
    "10001000": 450.0,   # Neoplasms benign, malignant and unspecified
    "10002000": 85.0,    # Blood and lymphatic system disorders
    "10003000": 320.0,   # Immune system disorders
    "10004000": 15.0,    # Endocrine disorders
    "10005000": 210.0,   # Metabolism and nutrition disorders
    "10006000": 55.0,    # Psychiatric disorders
    "10007000": 95.0,    # Nervous system disorders
    "10008000": 25.0,    # Eye disorders
    "10009000": 180.0,   # Ear and labyrinth disorders
    "10010000": 420.0,   # Cardiac disorders
    "10011000": 380.0,   # Vascular disorders
    "10012000": 650.0,   # Respiratory, thoracic and mediastinal disorders
    "10013000": 290.0,   # Gastrointestinal disorders
    "10014000": 110.0,   # Hepatobiliary disorders
    "10015000": 240.0,   # Skin and subcutaneous tissue disorders
    "10016000": 180.0,   # Musculoskeletal and connective tissue disorders
    "10017000": 95.0,    # Renal and urinary disorders
    "10018000": 65.0,    # Pregnancy, puerperium and perinatal conditions
    "10019000": 45.0,    # Reproductive system and breast disorders
    "10020000": 350.0,   # Congenital, familial and genetic disorders
    "10021000": 120.0,   # Ear and labyrinth disorders (duplicate check, usually merged)
    "10022000": 80.0,    # Injury, poisoning and procedural complications
    "10023000": 40.0,    # Surgical and medical procedures
    "10024000": 50.0,    # Social circumstances
    "10025000": 30.0,    # Investigations
    "10026000": 200.0,   # Product issues
    "10027000": 15.0,    # Administration site conditions
    "10028000": 10.0,    # Device related issues
    "10029000": 5.0,     # Off-label use
    "10030000": 2.0,     # Misuse
    "10031000": 1.0,     # Overdose
    "10032000": 3.0,     # Underdose
    "10033000": 4.0,     # Wrong technique in product usage process
    "10034000": 2.0,     # Medication error
    "10035000": 1.0,     # Dosage error
    "10036000": 1.0,     # Dose form error
    "10037000": 1.0,     # Drug administration error
    "10038000": 1.0,     # Drug error, unspecified
    "10039000": 1.0,     # Drug use, abuse, dependence, withdrawal
    "10040000": 1.0,     # Drug interactions
    "10041000": 1.0,     # Drug toxicity
    "10042000": 1.0,     # Drug hypersensitivity
    "10043000": 1.0,     # Drug intolerance
    "10044000": 1.0,     # Drug dependence
    "10045000": 1.0,     # Drug withdrawal
    "10046000": 1.0,     # Drug abuse
    "10047000": 1.0,     # Drug misuse
    "10048000": 1.0,     # Drug overdose
    "10049000": 1.0,     # Drug underdose
    "10050000": 1.0,     # Drug error, unspecified
    "10051000": 1.0,     # Drug use, abuse, dependence, withdrawal
    "10052000": 1.0,     # Drug interactions
    "10053000": 1.0,     # Drug toxicity
    "10054000": 1.0,     # Drug hypersensitivity
    "10055000": 1.0,     # Drug intolerance
    "10056000": 1.0,     # Drug dependence
    "10057000": 1.0,     # Drug withdrawal
    "10058000": 1.0,     # Drug abuse
    "10059000": 1.0,     # Drug misuse
    "10060000": 1.0,     # Drug overdose
    "10061000": 1.0,     # Drug underdose
    "10062000": 1.0,     # Drug error, unspecified
    "10063000": 1.0,     # Drug use, abuse, dependence, withdrawal
    "10064000": 1.0,     # Drug interactions
    "10065000": 1.0,     # Drug toxicity
    "10066000": 1.0,     # Drug hypersensitivity
    "10067000": 1.0,     # Drug intolerance
    "10068000": 1.0,     # Drug dependence
    "10069000": 1.0,     # Drug withdrawal
    "10070000": 1.0,     # Drug abuse
    "10071000": 1.0,     # Drug misuse
    "10072000": 1.0,     # Drug overdose
    "10073000": 1.0,     # Drug underdose
    "10074000": 1.0,     # Drug error, unspecified
    "10075000": 1.0,     # Drug use, abuse, dependence, withdrawal
    "10076000": 1.0,     # Drug interactions
    "10077000": 1.0,     # Drug toxicity
    "10078000": 1.0,     # Drug hypersensitivity
    "10079000": 1.0,     # Drug intolerance
    "10080000": 1.0,     # Drug dependence
    "10081000": 1.0,     # Drug withdrawal
    "10082000": 1.0,     # Drug abuse
    "10083000": 1.0,     # Drug misuse
    "10084000": 1.0,     # Drug overdose
    "10085000": 1.0,     # Drug underdose
    "10086000": 1.0,     # Drug error, unspecified
    "10087000": 1.0,     # Drug use, abuse, dependence, withdrawal
    "10088000": 1.0,     # Drug interactions
    "10089000": 1.0,     # Drug toxicity
    "10090000": 1.0,     # Drug hypersensitivity
    "10091000": 1.0,     # Drug intolerance
    "10092000": 1.0,     # Drug dependence
    "10093000": 1.0,     # Drug withdrawal
    "10094000": 1.0,     # Drug abuse
    "10095000": 1.0,     # Drug misuse
    "10096000": 1.0,     # Drug overdose
    "10097000": 1.0,     # Drug underdose
    "10098000": 1.0,     # Drug error, unspecified
    "10099000": 1.0,     # Drug use, abuse, dependence, withdrawal
    "10100000": 1.0,     # Drug interactions
    "10101000": 1.0,     # Drug toxicity
    "10102000": 1.0,     # Drug hypersensitivity
    "10103000": 1.0,     # Drug intolerance
    "10104000": 1.0,     # Drug dependence
    "10105000": 1.0,     # Drug withdrawal
    "10106000": 1.0,     # Drug abuse
    "10107000": 1.0,     # Drug misuse
    "10108000": 1.0,     # Drug overdose
    "10109000": 1.0,     # Drug underdose
    "10110000": 1.0,     # Drug error, unspecified
}

# Initialize directories on module import (optional, can be called explicitly)
# ensure_dirs()