import logging
import os
import sys
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_MODELS = PROJECT_ROOT / "data" / "models"
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"
SPECS_DIR = PROJECT_ROOT / "specs"

# Hyperparameters and Seeds
RANDOM_SEED = 42
MIN_ELEMENTS = 5
HOLDOUT_SIZE = 5000
NOVEL_SIZE = 5000

# Dataset Configuration
DATASET_HMAO_NAME = "hmao/all_apis_for_multiapi"
DATASET_HMAO_CHECKSUM = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" # Placeholder SHA256 (update if real hash known)
# Note: The actual SHA256 for the specific dataset version should be updated here once verified.
# For now, we use a placeholder to satisfy the config requirement.

def ensure_dirs():
    """Create required directory structure if it doesn't exist."""
    dirs = [DATA_RAW, DATA_PROCESSED, DATA_MODELS, CODE_DIR, TESTS_DIR, SPECS_DIR]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def setup_logging():
    """Configure basic logging infrastructure."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)
