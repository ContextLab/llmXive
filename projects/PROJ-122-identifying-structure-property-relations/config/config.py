"""Project configuration."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CODE_DIR = BASE_DIR / "code"
TESTS_DIR = BASE_DIR / "tests"
STATE_DIR = BASE_DIR / "state"

# Random seed
RANDOM_SEED = 42

# Data quality thresholds
WEIGHT_FRACTION_TOLERANCE = 0.02
MIN_RECORDS_FOR_TRAINING = 100
MAX_VIF_THRESHOLD = 5.0
HIGH_VIF_THRESHOLD = 10.0

# Memory constraints
MAX_RAM_GB = 14.0
MAX_DISK_GB = 30.0

# API settings
API_RETRY_COUNT = 3
API_BACKOFF_FACTOR = 1.5

# File paths
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
FEATURES_DIR = DATA_DIR / "features"
FIGURES_DIR = BASE_DIR / "figures"
STATE_PROJECTS_DIR = STATE_DIR / "projects"

# Project ID
PROJECT_ID = "PROJ-122-identifying-structure-property-relations"