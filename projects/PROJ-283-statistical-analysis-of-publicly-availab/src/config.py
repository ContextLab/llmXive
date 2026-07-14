"""
Project configuration constants.
"""
import os
from pathlib import Path

# Random seeds for reproducibility
RANDOM_SEED = 42

# Project root path
PROJECT_ROOT = Path(__file__).parent.parent

# Directory paths
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_RESULTS_DIR = DATA_DIR / "results"

SPECS_DIR = PROJECT_ROOT / "specs"
SPECS_CONTRACTS_DIR = SPECS_DIR / "contracts"

SRC_DIR = PROJECT_ROOT / "src"
TESTS_DIR = PROJECT_ROOT / "tests"

# Lichess dataset URL constants
LICHES_GAMES_URL = "https://database.lichess.org/standard/lichess_db-standard-rated-2024-01.pgn.zst"
LICHES_GAMES_URL_2023 = "https://database.lichess.org/standard/lichess_db-standard-rated-2023.pgn.zst"

def ensure_directories():
    """Create all required project directories if they don't exist."""
    directories = [
        DATA_DIR,
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        DATA_RESULTS_DIR,
        SPECS_DIR,
        SPECS_CONTRACTS_DIR,
        SRC_DIR,
        TESTS_DIR,
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    return directories
