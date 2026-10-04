"""
Configuration Constants (T004)

Defines global constants used across the pipeline.
"""

import os

# Project paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(PROJECT_ROOT, "data")
RAW_DATA_PATH = os.path.join(DATA_PATH, "raw", "smiles.csv")
PROCESSED_DATA_PATH = os.path.join(DATA_PATH, "processed")

# Model and algorithm parameters
SEED = 42
OUTLIER_SIGMA = 3.0
VIF_THRESHOLD = 10.0
TARGET_VAR = 'conductivity'  # Default target variable

# Sensitivity analysis thresholds
SENSITIVITY_THRESHOLDS = [2.5, 3.0, 3.5]

# Confidence interval target
CONFIDENCE_INTERVAL_TARGET = 0.95

# Logging
LOG_FILE = os.path.join(PROJECT_ROOT, "logs", "pipeline.log")

# Ensure directories exist
os.makedirs(DATA_PATH, exist_ok=True)
os.makedirs(PROCESSED_DATA_PATH, exist_ok=True)
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
