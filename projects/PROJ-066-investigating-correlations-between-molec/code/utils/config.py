"""
Configuration constants for the molecular descriptor pipeline.
"""
import os
from pathlib import Path

# Random seed for reproducibility
RANDOM_SEED = 42

# Resource constraints
MAX_MEMORY_GB = 7
MAX_DURATION_HOURS = 6

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"
STATE_DIR = PROJECT_ROOT / "state" / "projects"

# Ensure directories exist
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)
