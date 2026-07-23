"""
Configuration utilities for random seeds, paths, and constants.

This module provides centralized configuration for the llmXive research pipeline,
including project root detection, random seed management for reproducibility,
and constant definitions for molecular analysis parameters.
"""
import os
import random
from pathlib import Path
from typing import Dict, Any

# Project root is three levels up from this file (code/utils/config.py -> project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Default random seed for reproducibility
DEFAULT_SEED = 42

# Molecular analysis constants
# Per DEV-001: Conformer ensemble size reduced from 50 (Spec FR-003) to 20 for CPU feasibility
DEFAULT_CONFORMER_COUNT = 20

# Data paths relative to project root
DATA_RAW_DIR = "data/raw"
DATA_PROCESSED_DIR = "data/processed"
DATA_FIGURES_DIR = "figures"
STATE_DIR = "state/projects"
SPECS_DIR = "specs/001-molecular-flexibility-permeability"

# File paths
DEVIATION_RECORD_PATH = f"{STATE_DIR}/PROJ-266-exploring-the-correlation-between-molecu.yaml"
CHECKSUM_MANIFEST_PATH = f"{STATE_DIR}/checksums.json"
LOGS_DIR = "logs"

# Analysis constants
DEFAULT_OUTLIER_IQR_MULTIPLIER = 1.5
DEFAULT_FDR_Q_THRESHOLD = 0.05
DEFAULT_VIF_COLLINEARITY_THRESHOLD = 5.0

# Correlation method constants
CORRELATION_METHODS = ["pearson", "spearman"]

# Cross-validation constants
DEFAULT_CV_FOLDS = 5
DEFAULT_RANDOM_STATE = 42

def get_project_root() -> Path:
    """
    Return the absolute path to the project root directory.

    Returns:
        Path: The project root directory as a Path object.
    """
    return PROJECT_ROOT

def set_seed(seed: int = DEFAULT_SEED) -> None:
    """
    Set random seeds for reproducibility across Python, NumPy, and OS.

    This function ensures deterministic behavior by setting:
    - Python's random seed
    - PYTHONHASHSEED environment variable
    - Note: NumPy seed should be set separately where NumPy is imported

    Args:
        seed (int): The random seed value (default: 42).
    """
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_config_summary() -> Dict[str, Any]:
    """
    Return a summary of the current configuration state.

    This is useful for logging and reproducibility tracking.

    Returns:
        Dict[str, Any]: A dictionary containing configuration details.
    """
    return {
        "project_root": str(PROJECT_ROOT),
        "seed": DEFAULT_SEED,
        "conformer_count": DEFAULT_CONFORMER_COUNT,
        "data_raw_dir": str(PROJECT_ROOT / DATA_RAW_DIR),
        "data_processed_dir": str(PROJECT_ROOT / DATA_PROCESSED_DIR),
        "deviation_record_path": str(PROJECT_ROOT / DEVIATION_RECORD_PATH),
        "outlier_iqr_multiplier": DEFAULT_OUTLIER_IQR_MULTIPLIER,
        "fdr_q_threshold": DEFAULT_FDR_Q_THRESHOLD,
        "vif_threshold": DEFAULT_VIF_COLLINEARITY_THRESHOLD,
        "cv_folds": DEFAULT_CV_FOLDS
    }

def get_data_path(subdir: str = "processed", filename: str = "") -> Path:
    """
    Construct an absolute path to a data file.

    Args:
        subdir (str): Subdirectory under data/ (e.g., 'raw', 'processed').
        filename (str): The filename within the subdirectory.

    Returns:
        Path: The absolute path to the data file.
    """
    base_dir = PROJECT_ROOT / "data" / subdir
    if filename:
        return base_dir / filename
    return base_dir

def get_state_path(filename: str = "") -> Path:
    """
    Construct an absolute path to a state file.

    Args:
        filename (str): The filename within the state directory.

    Returns:
        Path: The absolute path to the state file.
    """
    base_dir = PROJECT_ROOT / STATE_DIR
    if filename:
        return base_dir / filename
    return base_dir

def get_figures_path(filename: str = "") -> Path:
    """
    Construct an absolute path to a figures file.

    Args:
        filename (str): The filename within the figures directory.

    Returns:
        Path: The absolute path to the figures file.
    """
    base_dir = PROJECT_ROOT / DATA_FIGURES_DIR
    if filename:
        return base_dir / filename
    return base_dir

def get_logs_path(filename: str = "") -> Path:
    """
    Construct an absolute path to a log file.

    Args:
        filename (str): The filename within the logs directory.

    Returns:
        Path: The absolute path to the log file.
    """
    base_dir = PROJECT_ROOT / LOGS_DIR
    if filename:
        return base_dir / filename
    return base_dir