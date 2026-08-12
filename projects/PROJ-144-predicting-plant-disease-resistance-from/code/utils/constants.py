"""
Project constants and configuration.
"""
import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Directory paths
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
TESTS_DIR = PROJECT_ROOT / "tests"
STATE_DIR = PROJECT_ROOT / "state"
RESULTS_DIR = PROJECT_ROOT / "results"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
SPEC_DIR = PROJECT_ROOT / "specs"

# Random seed for reproducibility
RANDOM_SEED = 42

# Model training parameters
HOLD_OUT_FRACTION = 0.20
MAX_FEATURES = 1000
MIN_SAMPLES_SPLIT = 2
MIN_SAMPLES_LEAF = 1

# Hypothesis thresholds
BALANCED_ACCURACY_THRESHOLD = 0.75
ROC_AUC_THRESHOLD = 0.80
PERMUTATION_P_VALUE_THRESHOLD = 0.05
FDR_THRESHOLD = 0.05
CORRELATION_THRESHOLD = 0.4
MISSING_THRESHOLD = 0.30
VIF_THRESHOLD = 5.0

# File paths for artifacts
ARTIFACT_HASHES_FILE = STATE_DIR / "artifact_hashes.yaml"
METADATA_SCHEMA_FILE = CONTRACTS_DIR / "metadata.schema.yaml"
OUTPUT_SCHEMA_FILE = CONTRACTS_DIR / "output.schema.yaml"

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
