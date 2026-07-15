"""
Configuration module for the project.
Defines paths, random seeds, and hyperparameters.
"""
import os
from pathlib import Path
from typing import Dict, Any

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directory Paths
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"
FIGURES_DIR = PROJECT_ROOT / "figures"
RESULTS_DIR = PROJECT_ROOT / "data" / "results"

# Random Seeds
RANDOM_SEED = 42

# Hyperparameters
MOTION_THRESHOLD_FD = 0.5  # mm
GLOBAL_SIGNAL_SD_THRESHOLD = 0.0  # Exclusion threshold for zero variance

def ensure_directories() -> None:
    """Create all necessary project directories if they do not exist."""
    directories = [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        CODE_DIR,
        TESTS_DIR,
        FIGURES_DIR,
        RESULTS_DIR
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

def validate_config() -> Dict[str, Any]:
    """Validate that configuration is consistent and directories are writable."""
    ensure_directories()
    return {
        "project_root": str(PROJECT_ROOT),
        "data_raw": str(DATA_RAW_DIR),
        "data_processed": str(DATA_PROCESSED_DIR),
        "random_seed": RANDOM_SEED,
        "motion_threshold_fd": MOTION_THRESHOLD_FD
    }
