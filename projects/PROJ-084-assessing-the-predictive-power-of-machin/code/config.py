"""
Configuration constants and utilities for the ML predictive power assessment pipeline.

This module centralizes:
- Random seeds for reproducibility
- File system paths (relative to project root)
- Hyperparameter grids for Random Forest and SVM
- Data processing constraints
"""
import os
from pathlib import Path
from typing import Dict, List, Any

# --- Reproducibility ---
RANDOM_SEED: int = 42
"""Global random seed for numpy, pandas, sklearn, and torch if applicable."""

# --- Paths ---
# Determine project root (assumed to be parent of 'code' directory)
_ROOT_DIR: Path = Path(__file__).resolve().parent.parent
"""Absolute path to the project root directory."""

DATA_RAW_DIR: Path = _ROOT_DIR / "data" / "raw"
"""Directory for raw, unprocessed data files."""

DATA_PROCESSED_DIR: Path = _ROOT_DIR / "data" / "processed"
"""Directory for cleaned, feature-engineered data files."""

DATA_RESULTS_DIR: Path = _ROOT_DIR / "data" / "results"
"""Directory for model outputs, metrics, and reports."""

CODE_DIR: Path = _ROOT_DIR / "code"
"""Directory containing source code."""

TESTS_DIR: Path = _ROOT_DIR / "tests"
"""Directory containing test suites."""

SPECS_DIR: Path = _ROOT_DIR / "specs"
"""Directory containing specification documents."""

# --- Memory Constraints ---
MAX_MEMORY_GB: float = 7.0
"""Maximum allowed memory usage in GB for batch processing."""

# --- Hyperparameter Grids ---
RF_GRID: Dict[str, List[Any]] = {
    "n_estimators": [50, 100, 200],
    "max_depth": [None, 10, 20, 30],
    "min_samples_split": [2, 5, 10],
    "random_state": [RANDOM_SEED]
}
"""Hyperparameter grid for Random Forest Regressor grid search."""

SVM_GRID: Dict[str, List[Any]] = {
    "C": [0.1, 1.0, 10.0],
    "kernel": ["linear", "rbf"],
    "gamma": ["scale", "auto"],
    "random_state": [RANDOM_SEED]
}
"""Hyperparameter grid for SVM Regressor grid search."""

# --- Data Processing ---
BATCH_SIZE: int = 10000
"""Number of rows to process in a single batch to manage memory."""

YIELD_COLUMN_NAME: str = "yield"
"""Standardized name for the yield column in datasets."""

SMILES_COLUMN_NAME: str = "smiles"
"""Standardized name for the SMILES string column."""

# --- Model Evaluation ---
METRICS: List[str] = ["r2", "rmse", "mae"]
"""List of metrics to compute during model evaluation."""

# --- Logging ---
LOG_LEVEL: str = "INFO"
"""Default logging level for the pipeline."""