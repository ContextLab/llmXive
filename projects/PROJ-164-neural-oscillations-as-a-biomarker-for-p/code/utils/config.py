"""
Configuration management for the Neural Oscillations TDCS Biomarker project.

This module defines all project-wide constants, paths, seeds, and thresholds
required for reproducibility and consistent execution across the pipeline.
"""
import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROJECT_ID = "PROJ-164-neural-oscillations-as-a-biomarker-for-p"

# Directory Paths
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_SYNTHETIC_DIR = PROJECT_ROOT / "data" / "synthetic"
MODELS_DIR = PROJECT_ROOT / "models"
LOGS_DIR = PROJECT_ROOT / "logs"
STATE_DIR = PROJECT_ROOT / "state" / "projects"
DOCS_DIR = PROJECT_ROOT / "docs"
SPECS_DIR = PROJECT_ROOT / "specs"
CONTRACTS_DIR = SPECS_DIR / "contracts"

# Ensure directories exist (optional initialization helper)
def ensure_dirs():
    """Create necessary directories if they do not exist."""
    for d in [DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_SYNTHETIC_DIR, 
              MODELS_DIR, LOGS_DIR, STATE_DIR, DOCS_DIR, CONTRACTS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

# Random Seeds for Reproducibility
SEED = 42
RANDOM_SEED = 42
NUMPY_SEED = 42

# Statistical Thresholds
ALPHA_THRESHOLD = 0.05  # Significance level p
R2_EXPECTED = 0.1       # Expected R-squared for power analysis
POWER_TARGET = 0.80     # 80% power
FDR_METHOD = "fdr_bh"   # Benjamini-Hochberg method name for statsmodels

# Neural Oscillation Bands (Hz)
BANDS = ['delta', 'theta', 'alpha', 'beta', 'gamma']
BAND_FREQUENCIES = {
    'delta': (1.0, 4.0),
    'theta': (4.0, 8.0),
    'alpha': (8.0, 13.0),
    'beta': (13.0, 30.0),
    'gamma': (30.0, 45.0)
}
LOWER_FREQ_HZ = 1.0
UPPER_FREQ_HZ = 45.0

# Power Analysis Parameters
MIN_SAMPLE_SIZE_DEFAULT = 50  # Default minimum subjects if not calculated
MAX_RUNTIME_HOURS = 6
MAX_RAM_GB = 7

# Data Constraints
BAD_CHANNEL_ZSCORE_THRESHOLD = 5.0
EPOCH_DURATION_SEC = 2.0
EPOCH_OVERLAP_SEC = 0.0

# State File Path for Checksums
STATE_FILE_PATH = STATE_DIR / f"{PROJECT_ID}.yaml"

# Manifest Path
VERIFIED_SOURCE_MANIFEST_PATH = PROJECT_ROOT / "data" / "processed" / "verified_source_manifest.json"
PRE_REGISTRATION_PATH = PROJECT_ROOT / "data" / "processed" / "pre-registration.json"

# Mode Flags
MODE_PRIMARY = "Primary"
MODE_DATA_INSUFFICIENT = "Data Insufficient"
MODE_UNDERPOWERED = "Underpowered"