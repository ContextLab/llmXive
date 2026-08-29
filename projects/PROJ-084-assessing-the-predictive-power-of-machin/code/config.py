"""
Configuration constants for the project.
"""

import os
from pathlib import Path
from typing import Dict, List, Any

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent

# Directories
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"

# Random Seeds
RANDOM_SEED = 42

# Hyperparameter Grids
RF_GRID: Dict[str, List[Any]] = {
    'n_estimators': [100, 200],
    'max_depth': [10, 20, None],
    'min_samples_split': [2, 5],
    'min_samples_leaf': [1, 2]
}

SVM_GRID: Dict[str, List[Any]] = {
    'C': [0.1, 1, 10],
    'kernel': ['linear', 'rbf'],
    'gamma': ['scale', 'auto']
}

# Ensure directories exist (called at import or setup)
def ensure_dirs():
    for d in [DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_RESULTS_DIR, CODE_DIR, TESTS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

# Initialize dirs on module load
ensure_dirs()
