"""
Configuration settings for the project.
"""
import os
from pathlib import Path
from typing import Dict, List, Any

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent

# Directory Paths
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_RESULTS_DIR = DATA_DIR / "results"
FIGURES_DIR = DATA_DIR / "figures"
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"
SPECS_DIR = PROJECT_ROOT / "specs"

# Ensure directories exist
def ensure_dirs():
    for d in [DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_RESULTS_DIR, FIGURES_DIR, CODE_DIR, TESTS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

# Random Seeds
RANDOM_SEED = 42

# Hyperparameter Grids
RF_GRID = {
    'n_estimators': [100, 200],
    'max_depth': [10, 20, None]
}

SVM_GRID = {
    'C': [0.1, 1.0, 10.0],
    'kernel': ['linear', 'rbf']
}

# Yield Parsing Strategy
# Options: 'midpoint' (convert 50-60% to 55.0), 'exclude' (drop rows with ranges)
YIELD_RANGE_STRATEGY = 'midpoint'

# Memory Constraints
MAX_RAM_GB = 7.0

# Initialize directories on import
ensure_dirs()

# Export
__all__ = [
    'PROJECT_ROOT', 'DATA_DIR', 'DATA_RAW_DIR', 'DATA_PROCESSED_DIR', 
    'DATA_RESULTS_DIR', 'FIGURES_DIR', 'CODE_DIR', 'TESTS_DIR', 'SPECS_DIR',
    'ensure_dirs', 'RANDOM_SEED', 'RF_GRID', 'SVM_GRID', 
    'YIELD_RANGE_STRATEGY', 'MAX_RAM_GB'
]
