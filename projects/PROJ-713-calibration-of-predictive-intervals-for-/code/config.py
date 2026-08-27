"""
Configuration module for the Calibration of Predictive Intervals project.
Defines constants for paths, hyperparameters, and random seeds.
"""
import os
from pathlib import Path

# Project Root
# Assumes this file is at code/config.py, so root is parent of parent
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directory Structure
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
LOG_DIR = PROJECT_ROOT / "logs"
TESTS_DIR = PROJECT_ROOT / "tests"

# Data Subdirectories
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"

# Hyperparameters
RANDOM_SEED = 42
TRAIN_SPLIT_RATIO = 0.80  # 80/20 split as per FR-001 override
TEST_SPLIT_RATIO = 0.20

# Model Hyperparameters
ARIMA_ORDER = (1, 1, 1)
PROPHET_UNCERTAINTY_SAMPLES = 1000
LSTM_HIDDEN_UNITS = 32
LSTM_MAX_EPOCHS = 50
LSTM_EARLY_STOPPING_PATIENCE = 5
LSTM_INITIAL_LEARNING_RATE = 0.01
LSTM_LEARNING_RATE_REDUCTION = 0.1
LSTM_MAX_RETRIES = 3

# Evaluation Parameters
CONFIDENCE_LEVELS = [0.80, 0.95]
BOOTSTRAP_RESAMPLES = 1000
SIGNIFICANCE_ALPHA = 0.05

# Ensure directories exist (lazy initialization helper)
def ensure_dirs():
    """Create necessary directories if they do not exist."""
    for dir_path in [DATA_RAW_DIR, DATA_PROCESSED_DIR, RESULTS_DIR, FIGURES_DIR, LOG_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)

# Initialize directories on import if desired, or call ensure_dirs() explicitly
# ensure_dirs()
