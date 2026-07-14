"""
Configuration module for the chess Elo analysis project.

Contains:
- Random seed settings
- File path constants
- Dataset URL constants
- Threshold parameters
"""
import os
from pathlib import Path

# Random seed for reproducibility
RANDOM_SEED = 42

# Dataset configuration
LICHES_DATASET_URL = "https://huggingface.co/datasets/lichess/lichess_db_standard_rated"

# Sample size for dataset verification (T009)
SAMPLE_SIZE = 1000

# Threshold for missing move_time metadata (T009)
# Per Plan.md: HALT if >5% of sampled games lack move_time
MISSING_MOVE_TIME_THRESHOLD = 0.05

# File paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
RESULTS_DIR = DATA_DIR / "results"
SPECS_DIR = BASE_DIR / "specs"
CONTRACTS_DIR = SPECS_DIR / "contracts"
TESTS_DIR = BASE_DIR / "tests"

def ensure_directories():
    """Create all required directories if they don't exist."""
    directories = [
        DATA_DIR,
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        RESULTS_DIR,
        SPECS_DIR,
        CONTRACTS_DIR,
        TESTS_DIR,
        BASE_DIR / "src",
        BASE_DIR / "src" / "data",
        BASE_DIR / "src" / "models",
        BASE_DIR / "src" / "validation",
        BASE_DIR / "src" / "reports",
        BASE_DIR / "tests" / "unit",
        BASE_DIR / "tests" / "integration",
        BASE_DIR / "tests" / "contract",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

# Initialize directories on module import
ensure_directories()
