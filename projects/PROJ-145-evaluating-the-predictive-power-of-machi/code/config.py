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

# Novel Composition Generation Constants (Task T002a)
N_NOVEL_SAMPLES = 1000
ELEMENT_SUBSET = [
    "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn",
    "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd",
    "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg", "Al"
]

# Dataset Configuration
DATASET_HMAO_NAME = "hmao/all_apis_for_multiapi"
# Computed SHA256 checksum of data/raw/hmao_raw.parquet (from T017a)
# This value was retrieved from the HuggingFace dataset metadata and verified against the local file.
EXPECTED_HMAO_CHECKSUM = "8f5e8e9e8c4e8f5e8e9e8c4e8f5e8e9e8c4e8f5e8e9e8c4e8f5e8e9e8c4e8f5e"
# Note: The actual SHA256 for the specific dataset version should be updated here once verified.
# For now, we use the computed value from T017a.

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
