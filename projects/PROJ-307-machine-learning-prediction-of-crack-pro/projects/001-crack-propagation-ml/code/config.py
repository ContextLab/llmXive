"""
Configuration management for the crack propagation prediction pipeline.
"""
import os
from pathlib import Path
from typing import Dict, Any, List

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Directory paths
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
FIGURES_DIR = PROJECT_ROOT / "figures"
LOGS_DIR = PROJECT_ROOT / "logs"
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"
SPECS_DIR = PROJECT_ROOT / "specs"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

# Default configuration
DEFAULT_CONFIG = {
    "random_seed": 42,
    "test_size": 0.2,
    "cv_folds": 5,
    "n_permutations": 1000,
    "max_memory_gb": 7,
    "data_sources": {
        "nasa": "https://ntrs.nasa.gov/api/citations/19900019124/downloads/19900019124.pdf",
        "nist": "https://www.nist.gov/materials-data-repository"
    }
}

def ensure_dirs() -> None:
    """Create all required directories if they don't exist."""
    dirs = [
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        FIGURES_DIR,
        LOGS_DIR,
        CODE_DIR,
        TESTS_DIR,
        SPECS_DIR,
        CONTRACTS_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_config_dict() -> Dict[str, Any]:
    """Return the default configuration dictionary."""
    return DEFAULT_CONFIG.copy()
