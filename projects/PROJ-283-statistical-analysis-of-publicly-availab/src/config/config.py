import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Configuration Constants
RANDOM_SEED = 42

# Directory Paths
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"
SPECS_DIR = PROJECT_ROOT / "specs"
SPECS_CONTRACTS_DIR = SPECS_DIR / "contracts"
TESTS_CONTRACT_DIR = PROJECT_ROOT / "tests" / "contract"
TESTS_UNIT_DIR = PROJECT_ROOT / "tests" / "unit"
TESTS_INTEGRATION_DIR = PROJECT_ROOT / "tests" / "integration"

# Lichess Dataset URL (Real source)
LICHESS_DATASET_URL = "https://database.lichess.org/standard/lichess_db-standard-rated-2023.pgn.zst"

def ensure_directories():
    """Create all required project directories if they do not exist."""
    dirs = [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        DATA_RESULTS_DIR,
        SPECS_CONTRACTS_DIR,
        TESTS_CONTRACT_DIR,
        TESTS_UNIT_DIR,
        TESTS_INTEGRATION_DIR,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    return True
