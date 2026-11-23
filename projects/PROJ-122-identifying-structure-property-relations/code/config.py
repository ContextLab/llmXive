import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent

# Directory Paths
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
FEATURES_DIR = DATA_DIR / "features"
TESTS_DIR = PROJECT_ROOT / "tests"
STATE_DIR = PROJECT_ROOT / "state"
PROJECTS_STATE_DIR = STATE_DIR / "projects"

# Project Specific
PROJECT_ID = "PROJ-122-identifying-structure-property-relations"
PROJECT_STATE_FILE = PROJECTS_STATE_DIR / f"{PROJECT_ID}.yaml"

# Configuration Defaults
RANDOM_SEED = 42
MAX_WORKERS = 4
TOLERANCE_WEIGHT_FRACTION = 0.02
JOIN_SUCCESS_THRESHOLD = 0.50
VIF_THRESHOLD = 5.0
MIN_DATASET_SIZE = 100
MAX_RAM_CAPACITY_GB = 7.0

# Ensure directories exist (called at import time or by setup)
def ensure_directories():
    for dir_path in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, 
                     FEATURES_DIR, TESTS_DIR, STATE_DIR, PROJECTS_STATE_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)

# Initialize directories immediately
ensure_directories()
