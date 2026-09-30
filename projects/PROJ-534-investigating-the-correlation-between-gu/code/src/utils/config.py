"""
Configuration management for the gut microbiome and cognitive flexibility study.
Handles project paths, random seed management, and directory initialization.
"""
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import logging

# Fixed random seed for reproducibility across the entire pipeline
SEED = 42

# Project root is the parent of the 'code' directory
# We assume the script is run from the project root, or we detect it via __file__
_CURRENT_FILE = Path(__file__).resolve()
_PROJECT_ROOT = _CURRENT_FILE.parent.parent.parent
_CODE_ROOT = _CURRENT_FILE.parent.parent

# Directory paths relative to project root
DATA_DIR = _PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
RESULTS_DIR = DATA_DIR / "results"
LOGS_DIR = _PROJECT_ROOT / "logs"
FIGURES_DIR = DATA_DIR / "figures"
CONTRACTS_DIR = _PROJECT_ROOT / "contracts"
SPECS_DIR = _PROJECT_ROOT / "specs"

# Logging configuration defaults
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def get_project_root() -> Path:
    """Return the project root directory."""
    return _PROJECT_ROOT


def get_code_root() -> Path:
    """Return the code source root directory."""
    return _CODE_ROOT


def get_data_dir() -> Path:
    """Return the main data directory."""
    return DATA_DIR


def get_raw_data_dir() -> Path:
    """Return the raw data directory."""
    return RAW_DATA_DIR


def get_processed_data_dir() -> Path:
    """Return the processed data directory."""
    return PROCESSED_DATA_DIR


def get_results_dir() -> Path:
    """Return the results data directory."""
    return RESULTS_DIR


def get_logs_dir() -> Path:
    """Return the logs directory."""
    return LOGS_DIR


def get_figures_dir() -> Path:
    """Return the figures directory."""
    return FIGURES_DIR


def set_global_seed(seed: int = SEED) -> None:
    """
    Set the random seed for reproducibility across numpy, random, and python.
    
    Args:
        seed: Integer seed value. Defaults to the module-level SEED.
    """
    random.seed(seed)
    np.random.seed(seed)
    # Note: os.environ['PYTHONHASHSEED'] = str(seed) if needed for full determinism


def ensure_directories() -> None:
    """
    Create all required project directories if they do not exist.
    This includes data/raw, data/processed, data/results, logs, and data/figures.
    """
    directories = [
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        RESULTS_DIR,
        LOGS_DIR,
        FIGURES_DIR,
        CONTRACTS_DIR,
        SPECS_DIR,
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def get_config() -> Dict[str, Any]:
    """
    Return a dictionary containing all configuration paths and settings.
    
    Returns:
        Dictionary with path objects and settings.
    """
    return {
        "project_root": _PROJECT_ROOT,
        "code_root": _CODE_ROOT,
        "data_dir": DATA_DIR,
        "raw_data_dir": RAW_DATA_DIR,
        "processed_data_dir": PROCESSED_DATA_DIR,
        "results_dir": RESULTS_DIR,
        "logs_dir": LOGS_DIR,
        "figures_dir": FIGURES_DIR,
        "contracts_dir": CONTRACTS_DIR,
        "seed": SEED,
    }


def get_path(*relative_parts: str) -> Path:
    """
    Construct a path relative to the project root.
    
    Args:
        *relative_parts: Parts of the relative path.
        
    Returns:
        Absolute Path object.
    """
    return _PROJECT_ROOT.joinpath(*relative_parts)


def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure the root logger for the project.
    
    Args:
        log_file: Optional filename relative to LOGS_DIR. If None, logs to stdout/stderr.
        
    Returns:
        The configured root logger.
    """
    logger = logging.getLogger()
    logger.setLevel(LOG_LEVEL)
    
    # Clear existing handlers to avoid duplicates in interactive environments
    if logger.handlers:
        logger.handlers.clear()
    
    formatter = logging.Formatter(LOG_FORMAT)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_path = LOGS_DIR / log_file
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger
