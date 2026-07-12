"""
constants.py: Fixed random seeds and standard file paths for the solubility project.
"""
import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Data Directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
ARTIFACTS_DIR = DATA_DIR / "artifacts"

# Specs Directory
SPECS_DIR = PROJECT_ROOT / "specs" / "001-predicting-solubility-in-mixed-solvents"

# Fixed Random Seeds
SEED_NUMPY = 42
SEED_PANDAS = 42
SEED_SKLEARN = 42
SEED_XGBOOST = 42
SEED_TORCH = 42

# Tolerances
COMPOSITION_TOLERANCE = 1e-6
IMPUTATION_RATE_THRESHOLD = 0.15
R_SQUARED_THRESHOLD = 0.70
JACCARD_SIMILARITY_TARGET = 0.6
SPEARMAN_STABILITY_TARGET = 0.8

# Resource Limits (GB)
RAM_LIMIT_GB = 7.0
DISK_LIMIT_GB = 14.0

# Model Settings
CV_FOLDS = 5
MAX_TRIAL_TIME_MINUTES = 30
BATCH_SIZE_RDKIT = 1000
