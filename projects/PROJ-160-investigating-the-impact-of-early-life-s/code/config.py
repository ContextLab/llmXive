"""
Configuration constants and paths for the ABCD Study analysis pipeline.

This module defines project-wide constants, random seeds, and file paths
required for reproducibility and consistent data handling across all
analysis scripts.

Constants are specifically tuned for ABCD Study Release 4.0.
"""

import os
from pathlib import Path
from typing import Final

# Project Root: Derived from the current file location (code/config.py)
# Ensures paths are relative to the project root regardless of execution context.
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent

# Random Seed Configuration
# CRITICAL: Must be set on line 12 as per task specification for reproducibility.
RANDOM_SEED: Final[int] = 42

# ABCD Study Release 4.0 Constants
# These values correspond to the specific release version and data dictionary.
ABCD_RELEASE_VERSION: Final[str] = "4.0"
ABCD_DATASET_NAME: Final[str] = "ABCD_Release_4.0"

# File Paths (Relative to PROJECT_ROOT)
# Raw data directory for downloaded ABCD files
DATA_RAW_DIR: Final[Path] = PROJECT_ROOT / "data" / "raw"

# Processed data directory for cleaned datasets and model outputs
DATA_PROCESSED_DIR: Final[Path] = PROJECT_ROOT / "data" / "processed"

# Figures directory for generated plots
FIGURES_DIR: Final[Path] = PROJECT_ROOT / "figures"

# Logs directory
LOGS_DIR: Final[Path] = PROJECT_ROOT / "logs"

# Contracts directory for schema definitions
CONTRACTS_DIR: Final[Path] = PROJECT_ROOT / "contracts"

# Code directory (useful for self-referencing if needed)
CODE_DIR: Final[Path] = PROJECT_ROOT / "code"

# Specific Output Filenames (Standardized)
CLEANED_DATASET_FILENAME: Final[str] = "cleaned_dataset.csv"
MODEL_RESULTS_JSON_FILENAME: Final[str] = "model_results.json"
MODEL_RESULTS_CSV_FILENAME: Final[str] = "model_results_summary.csv"
SENSITIVITY_REPORT_FILENAME: Final[str] = "sensitivity_report.csv"
ROBUSTNESS_REPORT_FILENAME: Final[str] = "robustness_report.json"

# Full Paths for Convenience
CLEANED_DATASET_PATH: Final[Path] = DATA_PROCESSED_DIR / CLEANED_DATASET_FILENAME
MODEL_RESULTS_JSON_PATH: Final[Path] = DATA_PROCESSED_DIR / MODEL_RESULTS_JSON_FILENAME
MODEL_RESULTS_CSV_PATH: Final[Path] = DATA_PROCESSED_DIR / MODEL_RESULTS_CSV_FILENAME
SENSITIVITY_REPORT_PATH: Final[Path] = DATA_PROCESSED_DIR / SENSITIVITY_REPORT_FILENAME
ROBUSTNESS_REPORT_PATH: Final[Path] = DATA_PROCESSED_DIR / ROBUSTNESS_REPORT_FILENAME

# Statistical Constants
# Standard alpha level for hypothesis testing
ALPHA_DEFAULT: Final[float] = 0.05
# Bonferroni correction factor (3 subfields: CA3, DG, Subiculum)
BONFERRONI_FACTOR: Final[int] = 3
# Corrected alpha threshold
ALPHA_CORRECTED: Final[float] = ALPHA_DEFAULT / BONFERRONI_FACTOR

# Data Quality Thresholds
# Minimum number of participants required for valid analysis
MIN_PARTICIPANTS: Final[int] = 100
# Maximum allowed missing value percentage per column
MAX_MISSING_PCT: Final[float] = 0.10

# MRI Specific Constants
# ICV (Intracranial Volume) normalization factor (implicit 1.0, but kept for clarity)
ICV_NORMALIZATION_FACTOR: Final[float] = 1.0

# Permutation Test Configuration
DEFAULT_PERMUTATIONS: Final[int] = 5000
DEFAULT_N_JOBS: Final[int] = -1  # Use all available cores

def get_project_root() -> Path:
    """Returns the project root directory path."""
    return PROJECT_ROOT

def ensure_directories() -> None:
    """Creates all necessary directories if they do not exist."""
    dirs = [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        FIGURES_DIR,
        LOGS_DIR,
        CONTRACTS_DIR,
        CODE_DIR,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)