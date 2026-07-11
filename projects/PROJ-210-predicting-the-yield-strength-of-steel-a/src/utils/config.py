"""
Configuration module for the Steel Yield Strength Prediction project.

Defines paths, random seeds, and threshold constants used throughout the pipeline.
"""
import os
from pathlib import Path
from typing import Final

# Project Root Path
# Assumes this file is at src/utils/config.py
_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent

# Directory Paths
SRC_DIR: Final[Path] = _PROJECT_ROOT / "src"
DATA_DIR: Final[Path] = _PROJECT_ROOT / "data"
DATA_RAW_DIR: Final[Path] = DATA_DIR / "raw"
DATA_PROCESSED_DIR: Final[Path] = DATA_DIR / "processed"
DATA_RESULTS_DIR: Final[Path] = DATA_DIR / "results"
FIGURES_DIR: Final[Path] = DATA_RESULTS_DIR / "figures"
SHAP_PLOTS_DIR: Final[Path] = DATA_RESULTS_DIR / "shap_summary_plots"
MODELS_DIR: Final[Path] = SRC_DIR / "models"
UTILS_DIR: Final[Path] = SRC_DIR / "utils"
TESTS_DIR: Final[Path] = _PROJECT_ROOT / "tests"
DOCS_DIR: Final[Path] = _PROJECT_ROOT / "docs"
SPECS_DIR: Final[Path] = _PROJECT_ROOT / "specs"

# Random Seeds for reproducibility
RANDOM_SEED: Final[int] = 42
NP_RANDOM_SEED: Final[int] = 42

# Threshold Constants for feature selection and significance testing
THRESHOLD_LOW: Final[float] = 0.01
THRESHOLD_MID: Final[float] = 0.05
THRESHOLD_HIGH: Final[float] = 0.10
THRESHOLDS: Final[list[float]] = [THRESHOLD_LOW, THRESHOLD_MID, THRESHOLD_HIGH]

# Literature Mining Configuration (for fallback logic)
LITERATURE_URLS: Final[list[str]] = [
    "https://www.sciencedirect.com/journal/materials-science-and-engineering-a",
    "https://link.springer.com/journal/11783", # JOM
    # Add specific open-access journal URLs as defined in project specs
]
LITERATURE_MINED_OUTPUT: Final[Path] = DATA_RAW_DIR / "literature_mined.csv"

# Model Training Configuration
DEFAULT_CV_FOLDS: Final[int] = 3
MIN_SAMPLES_FOR_FOLDS: Final[int] = 100
ALTERNATIVE_CV_FOLDS: Final[int] = 10
ALTERNATIVE_CV_REPEATS: Final[int] = 5

# Resource Constraints (Constitution VI)
MAX_RUNTIME_HOURS: Final[int] = 4
MAX_RAM_GB: Final[int] = 6

def ensure_directories() -> None:
    """
    Creates all required directories if they do not exist.
    """
    directories = [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        DATA_RESULTS_DIR,
        FIGURES_DIR,
        SHAP_PLOTS_DIR,
        MODELS_DIR,
        UTILS_DIR,
        TESTS_DIR,
        DOCS_DIR,
        SPECS_DIR,
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    # Verification script to ensure directories are created
    print("Ensuring project directories exist...")
    ensure_directories()
    print(f"Project Root: {_PROJECT_ROOT}")
    print(f"Data Directory: {DATA_DIR}")
    print(f"Thresholds: {THRESHOLDS}")
    print("Directories created successfully.")