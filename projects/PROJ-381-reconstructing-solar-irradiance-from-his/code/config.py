"""
Configuration module for the Solar Irradiance Reconstruction project.
Provides path management, random seeds, and constants.
"""
import os
from pathlib import Path
from typing import Final

from env_manager import setup_environment, get_data_path

# Ensure environment variables are loaded
setup_environment()

# Project root directory
PROJECT_ROOT: Final[Path] = Path(__file__).parent.parent

# Data directories
DATA_RAW_DIR: Final[Path] = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR: Final[Path] = PROJECT_ROOT / "data" / "processed"

# Code directories
CODE_MODELS_DIR: Final[Path] = PROJECT_ROOT / "code" / "models"
CODE_ANALYSIS_DIR: Final[Path] = PROJECT_ROOT / "code" / "analysis"
CODE_DATA_DIR: Final[Path] = PROJECT_ROOT / "code" / "data"

# Random seed for reproducibility
RANDOM_SEED: Final[int] = 42

# FR-002: Gap filling threshold (1 year in days)
GAP_THRESHOLD_DAYS: Final[int] = 365

# FR-009: Sensitivity analysis thresholds
SENSITIVITY_THRESHOLDS: Final[list[float]] = [0.01, 0.05, 0.1]

def ensure_directories() -> None:
    """
    Ensure all required project directories exist.
    Creates them if they don't exist.
    """
    directories = [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        CODE_MODELS_DIR,
        CODE_ANALYSIS_DIR,
        CODE_DATA_DIR,
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Ensured directory exists: {directory}")

if __name__ == "__main__":
    ensure_directories()
    print("All directories ensured.")
