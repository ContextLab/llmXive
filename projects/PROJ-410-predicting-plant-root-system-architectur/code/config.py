"""
Configuration module for the root architecture prediction pipeline.
Defines paths, random seeds, and default hyperparameters.
"""
import os
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directory paths
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_FIGURES_DIR = PROJECT_ROOT / "data" / "figures"
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
SPECS_DIR = PROJECT_ROOT / "specs"

# Random seed for reproducibility
RANDOM_SEED = 42

# Default Hyperparameters (Required by T007)
HYPERPARAMETERS = {
    "lasso": {
        "alphas": [0.01, 0.1, 1.0, 10.0],
        "l1_ratio": 1.0,  # Pure Lasso
        "max_iter": 10000
    },
    "elastic_net": {
        "alphas": [0.01, 0.1, 1.0, 10.0],
        "l1_ratio": [0.2, 0.5, 0.8],
        "max_iter": 10000
    },
    "random_forest": {
        "n_estimators": [100, 200],
        "max_depth": [5, 10, 20, None],
        "min_samples_split": [2, 5],
        "min_samples_leaf": [1, 2]
    },
    "gradient_boosting": {
        "n_estimators": [100, 200],
        "learning_rate": [0.01, 0.1],
        "max_depth": [3, 5, 7],
        "min_samples_split": [2, 5]
    },
    "pca": {
        "n_components": 0.95  # Keep 95% variance
    }
}

def ensure_directories():
    """Create all required directories if they do not exist."""
    dirs = [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        DATA_FIGURES_DIR,
        CODE_DIR,
        TESTS_DIR,
        CONTRACTS_DIR,
        SPECS_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    return dirs
