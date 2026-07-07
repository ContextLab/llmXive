"""
Configuration management for the llmXive Sports Prediction project.
Loads environment variables from .env and provides centralized access
to paths, random seeds, and model hyperparameters.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
# This is safe to run even if .env is missing (it just returns False)
load_dotenv()

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Environment Variables
DATA_PATH = Path(os.getenv("DATA_PATH", "data/raw")).resolve()
RANDOM_SEED = int(os.getenv("RANDOM_SEED", "42"))
CI_MODE = os.getenv("CI_MODE", "false").lower() == "true"

# Derived Paths
DATA_RAW_PATH = DATA_PATH
DATA_PROCESSED_PATH = PROJECT_ROOT / "data" / "processed"
ARTIFACTS_REPORTS_PATH = PROJECT_ROOT / "artifacts" / "reports"
ARTIFACTS_FIGURES_PATH = PROJECT_ROOT / "artifacts" / "figures"
STATE_PATH = PROJECT_ROOT / "state"
LOGS_PATH = PROJECT_ROOT / "artifacts" / "logs"

# Hyperparameters
# General
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "1000"))
VERBOSE = os.getenv("VERBOSE", "true").lower() == "true"

# Logistic Regression
LR_SOLVER = os.getenv("LR_SOLVER", "lbfgs")
LR_MAX_ITER = int(os.getenv("LR_MAX_ITER", "1000"))
LR_C = float(os.getenv("LR_C", "1.0"))

# Random Forest
RF_N_ESTIMATORS = int(os.getenv("RF_N_ESTIMATORS", "100"))
RF_MAX_DEPTH = int(os.getenv("RF_MAX_DEPTH", "None")) if os.getenv("RF_MAX_DEPTH", "None") != "None" else None
RF_MIN_SAMPLES_SPLIT = int(os.getenv("RF_MIN_SAMPLES_SPLIT", "2"))
RF_MIN_SAMPLES_LEAF = int(os.getenv("RF_MIN_SAMPLES_LEAF", "1"))
RF_MAX_FEATURES = os.getenv("RF_MAX_FEATURES", "sqrt")

# XGBoost (Gradient Boosting)
XGB_N_ESTIMATORS = int(os.getenv("XGB_N_ESTIMATORS", "100"))
XGB_MAX_DEPTH = int(os.getenv("XGB_MAX_DEPTH", "6"))
XGB_LEARNING_RATE = float(os.getenv("XGB_LEARNING_RATE", "0.1"))
XGB_SUBSAMPLE = float(os.getenv("XGB_SUBSAMPLE", "1.0"))
XGB_COLSAMPLE_BYTREE = float(os.getenv("XGB_COLSAMPLE_BYTREE", "1.0"))
XGB_MIN_CHILD_WEIGHT = float(os.getenv("XGB_MIN_CHILD_WEIGHT", "1"))
XGB_EARLY_STOPPING_ROUNDS = int(os.getenv("XGB_EARLY_STOPPING_ROUNDS", "10"))

# Statistical Analysis
SIGNIFICANCE_LEVEL = float(os.getenv("SIGNIFICANCE_LEVEL", "0.05"))
DM_TEST_TYPE = os.getenv("DM_TEST_TYPE", "harvey") # Options: harvey, standard, adjusted

# Data Pipeline
TRAIN_END_YEAR = int(os.getenv("TRAIN_END_YEAR", "2018"))
TEST_START_YEAR = int(os.getenv("TEST_START_YEAR", "2019"))
PANDEMONIUM_EXCLUSION_YEAR = int(os.getenv("PANDEMONIUM_EXCLUSION_YEAR", "2020"))
COMPLETENESS_THRESHOLD = float(os.getenv("COMPLETENESS_THRESHOLD", "0.95"))

# Sensitivity Analysis
THRESHOLD_STEP = float(os.getenv("THRESHOLD_STEP", "0.01"))

# Ensure directories exist
def ensure_directories():
    """Create required directories if they do not exist."""
    directories = [
        DATA_RAW_PATH,
        DATA_PROCESSED_PATH,
        ARTIFACTS_REPORTS_PATH,
        ARTIFACTS_FIGURES_PATH,
        STATE_PATH,
        LOGS_PATH
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)