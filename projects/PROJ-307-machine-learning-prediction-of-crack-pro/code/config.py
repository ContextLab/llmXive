"""
Configuration module for hyperparameters, random seeds, and path settings.

This module centralizes all project-wide constants, default model parameters,
and directory paths to ensure consistency across the pipeline.
"""
import os
from pathlib import Path
from typing import Dict, Any, List

# Project Root
# Assumes this file is at code/config.py, so root is parent of parent
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directory Paths
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"
SPECS_DIR = PROJECT_ROOT / "specs"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
FIGURES_DIR = PROJECT_ROOT / "figures"
LOGS_DIR = PROJECT_ROOT / "logs"
MODELS_DIR = PROJECT_ROOT / "models"

# Hyperparameters & Random Seeds
RANDOM_SEED = 42
TEST_SIZE = 0.2
CV_FOLDS = 5

# Data Loading & Processing
MAX_ROWS = None  # None means load all
MISSING_VALUE_THRESHOLD = 0.5  # Drop columns with >50% missing

# Model Defaults - Baseline (Paris Law)
BASELINE_MAX_ITER = 1000
BASELINE_TOL = 1e-4

# Model Defaults - Random Forest
RF_N_ESTIMATORS = 100
RF_MAX_DEPTH = 10
RF_MIN_SAMPLES_SPLIT = 2
RF_MIN_SAMPLES_LEAF = 1
RF_MIN_WEIGHT_FRACTION_SPLIT = 0.0

# Model Defaults - XGBoost
XGB_N_ESTIMATORS = 100
XGB_MAX_DEPTH = 6
XGB_LEARNING_RATE = 0.1
XGB_SUBSAMPLE = 1.0
XGB_COLSAMPLE_BY_TREE = 1.0
XGB_MIN_CHILD_WEIGHT = 1
XGB_GAMMA = 0.0

# Model Defaults - Optuna Search Space
OPTUNA_N_TRIALS = 50
OPTUNA_TIMEOUT = 3600  # 1 hour
OPTUNA_PRUNING_PATIENCE = 10

# Validation Thresholds
MIN_R2_THRESHOLD = 0.0
SIGNIFICANCE_LEVEL = 0.05
PERMUTATION_N_PERMUTATIONS = 100  # Reduced for speed in CI, increase for production
PERMUTATION_RANDOM_STATE = RANDOM_SEED

# Feature Engineering
LOG_TRANSFORM_TARGET = True
LOG_TRANSFORM_FEATURES = True
LOG_FEATURES = ["delta_k"]  # Features to log-transform
LOG_TARGET = "da_dn"

# Regime Analysis (Ruptures)
REGIME_METHOD = "binseg"  # 'binseg', 'dynp', 'pelt'
REGIME_MODEL = "l2"  # 'l2', 'l1', 'rbf'
REGIME_BKPS_MAX = 3  # Maximum number of breakpoints to detect

# Output Settings
FIGURE_DPI = 150
FIGURE_FORMAT = "png"
REPORT_FORMAT = "html"

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def ensure_dirs() -> None:
    """Create all required directories if they do not exist."""
    dirs: List[Path] = [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        FIGURES_DIR,
        LOGS_DIR,
        SPECS_DIR,
        CONTRACTS_DIR,
        MODELS_DIR,
        TESTS_DIR,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_config_dict() -> Dict[str, Any]:
    """Return a dictionary of all configuration values for serialization/logging."""
    return {
        "random_seed": RANDOM_SEED,
        "test_size": TEST_SIZE,
        "cv_folds": CV_FOLDS,
        "baseline_max_iter": BASELINE_MAX_ITER,
        "rf_n_estimators": RF_N_ESTIMATORS,
        "rf_max_depth": RF_MAX_DEPTH,
        "xgb_n_estimators": XGB_N_ESTIMATORS,
        "xgb_max_depth": XGB_MAX_DEPTH,
        "xgb_learning_rate": XGB_LEARNING_RATE,
        "significance_level": SIGNIFICANCE_LEVEL,
        "perm_n_permutations": PERMUTATION_N_PERMUTATIONS,
        "figure_dpi": FIGURE_DPI,
        "log_level": LOG_LEVEL,
    }