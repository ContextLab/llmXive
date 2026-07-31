"""
Configuration module for the HEA project.
"""
import logging
import os
import sys
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_MODELS_DIR = DATA_DIR / "models"
CODE_DIR = BASE_DIR / "code"
TESTS_DIR = BASE_DIR / "tests"
SPECS_DIR = BASE_DIR / "specs"

# Ensure directories exist
def ensure_dirs():
    for directory in [DATA_DIR, DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_MODELS_DIR, CODE_DIR, TESTS_DIR, SPECS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

# Logging setup
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

# Hyperparameters and seeds
RANDOM_SEED = 42
N_ESTIMATORS = 100
MAX_DEPTH = 10

# Dataset constants
DATASET_NAME = "hmao/all_apis_for_multiapi"
# Placeholder for checksum if needed later
DATASET_CHECKSUM = None
