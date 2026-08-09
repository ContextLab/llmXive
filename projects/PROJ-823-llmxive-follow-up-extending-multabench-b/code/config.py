"""
Global configuration and paths for the project.
"""
import os
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Seeds
RANDOM_SEED = 42
SENSITIVITY_SEEDS = [42, 123, 456, 789, 101112]

# Paths
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
ARTIFACTS_DIR = DATA_DIR / "artifacts"
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"

def ensure_directories():
    """Creates necessary directories if they do not exist."""
    for dir_path in [RAW_DATA_DIR, PROCESSED_DATA_DIR, ARTIFACTS_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)