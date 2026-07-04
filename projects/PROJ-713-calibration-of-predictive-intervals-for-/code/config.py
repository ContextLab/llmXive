import os
from pathlib import Path

# Determine the project root. Assuming this file is at code/config.py,
# the project root is the parent of the parent of this file's directory
# if we are in a nested structure, but based on the task description
# "projects/PROJ-713-.../code/", the config is inside 'code'.
# We assume the script is run from the project root or config adjusts accordingly.
# Standard pattern: Project Root is where data/, code/, results/ live.

# If this file is at <root>/code/config.py
_THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = _THIS_FILE.parent.parent

# Ensure the project root is valid
if not PROJECT_ROOT.exists():
    raise FileNotFoundError(f"Project root not found at {PROJECT_ROOT}")

# Directory Paths
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = PROJECT_ROOT / "figures"
LOG_DIR = PROJECT_ROOT / "logs"
TESTS_DIR = PROJECT_ROOT / "tests"

# Hyperparameters and Defaults
RANDOM_SEED = 42
TRAIN_SPLIT_RATIO = 0.80  # 80/20 split as per spec
VALIDATION_SPLIT_RATIO = 0.0  # Handled via time-series split usually

# Model Defaults
ARIMA_ORDER = (1, 1, 1)
PROPHET_UNCERTAINTY_SAMPLES = 1000
LSTM_HIDDEN_UNITS = 32
LSTM_MAX_EPOCHS = 50
LSTM_EARLY_STOPPING_PATIENCE = 5
LSTM_LEARNING_RATE = 0.01

# Evaluation Defaults
CONFIDENCE_LEVELS = [0.80, 0.95]
BOOTSTRAP_RESAMPLES = 1000
SIGNIFICANCE_ALPHA = 0.05

# Data Sources
M4_URL = "https://github.com/Mcompetitions/M4-methods/raw/master/Dataset/Hourly/Hourly.csv"
UCI_ELECTRICITY_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/00321/LD2011_2014.txt"

# Checksums (placeholders - would be updated with real values)
M4_CHECKSUM = None
UCI_ELECTRICITY_CHECKSUM = None
