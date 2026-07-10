import os
import numpy as np

# Set random seed for reproducibility
np.random.seed(42)

# Project root directory (assumed to be the parent of code/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Data directories
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DATA_RAW_DIR = os.path.join(DATA_DIR, "raw")
DATA_PROCESSED_DIR = os.path.join(DATA_DIR, "processed")

# Ensure directories exist
os.makedirs(DATA_RAW_DIR, exist_ok=True)
os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)

# Hyperparameters
MIN_WORD_COUNT = 50
LANGUAGE_DETECTION_THRESHOLD = 0.8
SIMILARITY_THRESHOLD_DEFAULT = 0.30
VIF_WARNING_THRESHOLD = 5.0

# Output paths
OUTPUT_REGRESSION_PLOT = os.path.join(PROJECT_ROOT, "artifacts", "regression_plot.png")
