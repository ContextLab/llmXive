"""
Global configuration constants, random seeds, and path definitions for the llmXive
alloy diffusion prediction pipeline.
"""

import os
from pathlib import Path
from typing import Final

# Project Root
PROJECT_ROOT: Final = Path(__file__).resolve().parent.parent

# Directory Paths
CODE_DIR: Final = PROJECT_ROOT / "code"
DATA_DIR: Final = PROJECT_ROOT / "data"
DATA_RAW_DIR: Final = DATA_DIR / "raw"
DATA_CURATED_DIR: Final = DATA_DIR / "curated"
DATA_ARTIFACTS_DIR: Final = DATA_DIR / "artifacts"
DATA_LOGS_DIR: Final = DATA_DIR / "logs"
ERRORS_DIR: Final = PROJECT_ROOT / "errors"
MODELS_DIR: Final = PROJECT_ROOT / "models"
REPORTS_DIR: Final = PROJECT_ROOT / "reports"
FIGURES_DIR: Final = PROJECT_ROOT / "figures"
TESTS_DIR: Final = PROJECT_ROOT / "tests"
SPECS_DIR: Final = PROJECT_ROOT / "specs"

# File Paths
RAW_DIFFUSION_FILE: Final = DATA_RAW_DIR / "fetched_diffusion.csv"
FILTERED_DATA_FILE: Final = DATA_CURATED_DIR / "filtered.csv"
EXCLUSION_LOG_FILE: Final = DATA_LOGS_DIR / "exclusions.log"
MISSING_ATOMIC_DATA_FILE: Final = ERRORS_DIR / "missing_atomic_data.csv"
VALIDATION_REPORT_FILE: Final = REPORTS_DIR / "validation_report.json"
FINAL_RF_MODEL_FILE: Final = MODELS_DIR / "final_rf.pkl"
FINAL_GB_MODEL_FILE: Final = MODELS_DIR / "final_gb.pkl"
LINEAR_COEF_FILE: Final = MODELS_DIR / "linear_coef.json"

# Random Seeds
RANDOM_SEED: Final = 42
NESTED_RANDOM_SEED: Final = 123

# Model Hyperparameters (Defaults)
RF_MAX_DEPTH: Final = 10
RF_N_ESTIMATORS: Final = 100
GB_MAX_DEPTH: Final = 5
GB_N_ESTIMATORS: Final = 100
CV_FOLDS: Final = 5

# Thresholds
MIN_DATASET_SIZE: Final = 50
P_VALUE_THRESHOLD: Final = 0.05
R2_LOW_POWER_THRESHOLD: Final = 0.1
CLASSIFICATION_THRESHOLD: Final = 0.5  # eV, default baseline for sensitivity analysis

# API Keys & Environment
MP_API_KEY_ENV_VAR: Final = "MP_API_KEY"
DEFAULT_TIMEOUT: Final = 30  # seconds

# Logging
LOG_LEVEL: Final = "INFO"
LOG_FORMAT: Final = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Constants for Feature Engineering
SIZE_MISMATCH_THRESHOLD_LOW: Final = -0.15
SIZE_MISMATCH_THRESHOLD_HIGH: Final = 0.15

def ensure_directories():
    """Create all required directories if they do not exist."""
    dirs = [
        DATA_RAW_DIR, DATA_CURATED_DIR, DATA_ARTIFACTS_DIR, DATA_LOGS_DIR,
        ERRORS_DIR, MODELS_DIR, REPORTS_DIR, FIGURES_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# Initialize directories on import if needed (optional, can be called explicitly)
# ensure_directories()
