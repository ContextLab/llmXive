"""
Configuration module for hyperparameters, paths, and random seeds.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data paths
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_OUTPUT_DIR = PROJECT_ROOT / "data" / "output"

# Output paths
FIGURES_DIR = PROJECT_ROOT / "figures"
LOGS_DIR = PROJECT_ROOT / "logs"
MODELS_DIR = PROJECT_ROOT / "models"

# Hyperparameters
RANDOM_SEED = 42
TEST_SIZE = 0.2
CV_FOLDS = 5

# Thresholds
MIN_SAMPLES_PER_FAMILY = 50
MAX_MISSING_RATIO = 0.20
OUTLIER_SIGMA = 3.0

def ensure_dirs() -> None:
    """
    Create all required directories if they do not exist.
    """
    dirs = [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        DATA_OUTPUT_DIR,
        FIGURES_DIR,
        LOGS_DIR,
        MODELS_DIR,
        PROJECT_ROOT / "code" / "data",
        PROJECT_ROOT / "code" / "models",
        PROJECT_ROOT / "code" / "utils",
        PROJECT_ROOT / "tests",
        PROJECT_ROOT / "docs",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
