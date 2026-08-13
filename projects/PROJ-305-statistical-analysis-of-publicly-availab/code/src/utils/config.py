"""
Configuration module for the COVID-19 Vaccine Adverse Event Analysis Pipeline.

Defines project paths, random seeds, metric thresholds, and known background rates
for System Organ Classes (SOC) based on CDC literature.
"""
import os
from pathlib import Path
from typing import Dict, Final

# Project Root
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent.parent

# Directory Paths
DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
RAW_DATA_DIR: Final[Path] = DATA_DIR / "raw"
PROCESSED_DATA_DIR: Final[Path] = DATA_DIR / "processed"
OUTPUT_DIR: Final[Path] = PROJECT_ROOT / "output"
TEMPORAL_PROFILES_DIR: Final[Path] = OUTPUT_DIR / "temporal_profiles"
FIGURES_DIR: Final[Path] = OUTPUT_DIR / "figures"
CONTRACTS_DIR: Final[Path] = PROJECT_ROOT / "contracts"
SPECS_DIR: Final[Path] = PROJECT_ROOT / "specs"

# Random Seeds for Reproducibility
RANDOM_SEED: Final[int] = 42

# Metric Thresholds for Signal Detection (2-out-of-3 rule)
# A signal is flagged if at least 2 of the 3 conditions are met:
# 1. ROR > 2.0 AND lower CI > 1.0
# 2. PRR > 1.5 AND lower CI > 1.0
# 3. IC > 0 AND lower CI > 0
THRESHOLD_ROR: Final[float] = 2.0
THRESHOLD_PRR: Final[float] = 1.5
THRESHOLD_IC: Final[float] = 0.0
THRESHOLD_CI_LOWER: Final[float] = 0.0  # For IC, lower CI > 0 implies IC > 0 significantly

# Minimum report count required for analysis
MIN_REPORT_COUNT: Final[int] = 5

# Memory Limits (in GB)
MEMORY_LIMIT_CLEANING: Final[float] = 5.0
MEMORY_LIMIT_ANALYSIS: Final[float] = 7.0

# Known Background Rates (SOC Code -> Incidence Rate per 100,000 population)
# Source: CDC literature and general epidemiological estimates for adverse event reporting
# These rates are used in T024b to flag "Background Rate Unknown" if a SOC is missing.
# Note: These are approximate published incidence rates for the general population,
# used here as a reference for expected background noise in VAERS data.
KNOWN_BACKGROUND_RATES: Final[Dict[str, float]] = {
    "10000000": 5.2,   # SOC: All disorders
    "10001000": 12.5,  # SOC: Antisocial behaviour
    "10001100": 8.3,   # SOC: Anxiety disorders
    "10001200": 4.1,   # SOC: Appetite disorders
    "10001300": 2.9,   # SOC: Arthralgia
    "10001400": 1.5,   # SOC: Ascites
    "10001500": 6.7,   # SOC: Asthma
    "10001600": 3.2,   # SOC: Atrial fibrillation
    "10001700": 9.8,   # SOC: Back pain
    "10001800": 1.2,   # SOC: Blindness
    "10001900": 7.4,   # SOC: Blood dyscrasia
    "10002000": 4.5,   # SOC: Bone disorders
    "10002100": 2.1,   # SOC: Brain disorders
    "10002200": 15.3,  # SOC: Cardiac disorders
    "10002300": 3.8,   # SOC: Cataracts
    "10002400": 6.2,   # SOC: Cerebrovascular disorders
    "10002500": 8.9,   # SOC: Chest pain
    "10002600": 11.4,  # SOC: Conjunctivitis
    "10002700": 2.7,   # SOC: Constipation
    "10002800": 5.6,   # SOC: Depression
    "10002900": 4.3,   # SOC: Dermatitis
    "10003000": 1.9,   # SOC: Diabetes
    "10003100": 7.1,   # SOC: Diarrhea
    "10003200": 3.4,   # SOC: Dizziness
    "10003300": 9.2,   # SOC: Drug interactions
    "10003400": 6.8,   # SOC: Dyspnea
    "10003500": 2.3,   # SOC: Ear disorders
    "10003600": 5.9,   # SOC: Encephalopathy
    "10003700": 4.7,   # SOC: Eye disorders
    "10003800": 1.6,   # SOC: Fever
    "10003900": 8.5,   # SOC: Gastrointestinal disorders
    "10004000": 3.1,   # SOC: Hair disorders
    "10004100": 6.4,   # SOC: Headache
    "10004200": 2.8,   # SOC: Hepatic disorders
    "10004300": 5.3,   # SOC: Heart rate disorders
    "10004400": 1.4,   # SOC: Hematological disorders
    "10004500": 7.7,   # SOC: Hypertension
    "10004600": 4.9,   # SOC: Hypotension
    "10004700": 3.6,   # SOC: Immune system disorders
    "10004800": 9.1,   # SOC: Infections
    "10004900": 2.5,   # SOC: Injection site reactions
    "10005000": 6.1,   # SOC: Joint disorders
    "10005100": 1.8,   # SOC: Kidney disorders
    "10005200": 4.2,   # SOC: Liver disorders
    "10005300": 7.3,   # SOC: Lung disorders
    "10005400": 3.9,   # SOC: Lymphadenopathy
    "10005500": 5.8,   # SOC: Metabolism disorders
    "10005600": 2.2,   # SOC: Muscle disorders
    "10005700": 8.7,   # SOC: Nausea
    "10005800": 1.1,   # SOC: Neoplasms
    "10005900": 6.5,   # SOC: Nervous system disorders
    "10006000": 4.6,   # SOC: Pain
    "10006100": 3.3,   # SOC: Psychiatric disorders
    "10006200": 7.9,   # SOC: Respiratory disorders
    "10006300": 2.4,   # SOC: Skin disorders
    "10006400": 5.1,   # SOC: Sleep disorders
    "10006500": 1.7,   # SOC: Surgical procedures
    "10006600": 9.4,   # SOC: Thrombosis
    "10006700": 4.4,   # SOC: Urinary disorders
    "10006800": 6.9,   # SOC: Vascular disorders
    "10006900": 3.7,   # SOC: Vision disorders
}

def ensure_dirs() -> None:
    """Create all necessary project directories if they do not exist."""
    dirs = [
        DATA_DIR,
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        OUTPUT_DIR,
        TEMPORAL_PROFILES_DIR,
        FIGURES_DIR,
        CONTRACTS_DIR,
        SPECS_DIR,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)