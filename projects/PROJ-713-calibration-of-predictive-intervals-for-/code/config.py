"""
Configuration module for the project.
Defines paths, hyperparameters, and random seeds.
"""
import os
from pathlib import Path

# Determine project root (assumes this file is at code/config.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directories
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
LOG_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist (lazy creation handled by setup_data_dirs.py)
# But we define them here for import consistency

# Hyperparameters
RANDOM_SEED = 42
TEST_SIZE = 0.2  # 20% for test set
TRAIN_SIZE = 0.8  # 80% for training (derived from 1 - TEST_SIZE)

# Model Hyperparameters
ARIMA_ORDER = (1, 1, 1)
PROPHET_UNCERTAINTY_SAMPLES = 1000
LSTM_HIDDEN_UNITS = 32
LSTM_MAX_EPOCHS = 50
LSTM_EARLY_STOPPING_PATIENCE = 5
LSTM_LEARNING_RATE = 0.01

# Evaluation Parameters
CONFIDENCE_LEVELS = [0.80, 0.95]
BOOTSTRAP_RESAMPLES = 1000
SIGNIFICANCE_ALPHA = 0.05

# Logging
LOG_LEVEL = "INFO"
