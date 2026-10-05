"""
Configuration module for the gut microbiome and cognitive flexibility study.
Provides fixed random seeds, path configurations, and utility functions for
directory management and logging setup.
"""

import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, List
import numpy as np
import logging


# --- Fixed Random Seeds ---
RANDOM_SEED = 42

# --- Path Configurations (Relative to Project Root) ---
# Project root is assumed to be the directory containing 'code/'
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CODE_ROOT = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
RESULTS_DIR = DATA_DIR / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
LOGS_DIR = PROJECT_ROOT / "logs"

# --- Global Configuration State ---
_config: Dict[str, Any] = {
    "seed": RANDOM_SEED,
    "paths": {
        "project_root": PROJECT_ROOT,
        "code_root": CODE_ROOT,
        "data_dir": DATA_DIR,
        "raw_data_dir": RAW_DATA_DIR,
        "processed_data_dir": PROCESSED_DATA_DIR,
        "results_dir": RESULTS_DIR,
        "figures_dir": FIGURES_DIR,
        "logs_dir": LOGS_DIR,
    }
}


def set_seed(seed: int = RANDOM_SEED) -> None:
    """
    Set the random seed for reproducibility across numpy, random, and python's
    built-in random module.

    Args:
        seed: Integer seed value. Defaults to RANDOM_SEED (42).
    """
    global _config
    _config["seed"] = seed
    random.seed(seed)
    np.random.seed(seed)
    # Note: If using torch, tensorflow, or other libraries, set their seeds here too


def get_project_root() -> Path:
    """Return the project root directory."""
    return _config["paths"]["project_root"]


def get_code_root() -> Path:
    """Return the code source root directory."""
    return _config["paths"]["code_root"]


def get_data_dir() -> Path:
    """Return the main data directory."""
    return _config["paths"]["data_dir"]


def get_raw_data_dir() -> Path:
    """Return the raw data directory."""
    return _config["paths"]["raw_data_dir"]


def get_processed_data_dir() -> Path:
    """Return the processed data directory."""
    return _config["paths"]["processed_data_dir"]


def get_results_dir() -> Path:
    """Return the results directory."""
    return _config["paths"]["results_dir"]


def get_logs_dir() -> Path:
    """Return the logs directory."""
    return _config["paths"]["logs_dir"]


def get_figures_dir() -> Path:
    """Return the figures directory."""
    return _config["paths"]["figures_dir"]


def get_path(key: str) -> Path:
    """
    Retrieve a path by key from the configuration.

    Args:
        key: One of 'project_root', 'code_root', 'data_dir', 'raw_data_dir',
             'processed_data_dir', 'results_dir', 'logs_dir', 'figures_dir'.

    Returns:
        Path object for the requested directory.

    Raises:
        KeyError: If the key is not found in configuration.
    """
    if key not in _config["paths"]:
        raise KeyError(f"Path key '{key}' not found in configuration.")
    return _config["paths"][key]


def ensure_directories() -> None:
    """
    Ensure all required directories exist. Creates them if they do not exist.
    """
    paths = [
        get_data_dir(),
        get_raw_data_dir(),
        get_processed_data_dir(),
        get_results_dir(),
        get_figures_dir(),
        get_logs_dir(),
    ]
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def get_config() -> Dict[str, Any]:
    """Return the current configuration dictionary."""
    return _config


def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Configure the root logger for the project.

    Args:
        log_level: Logging level (e.g., logging.INFO, logging.DEBUG).
        log_file: Optional filename for log output. Defaults to 'pipeline.log' in logs_dir.

    Returns:
        The configured root logger.
    """
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler (if log file specified or default)
    if log_file:
        log_path = Path(log_file)
    else:
        log_path = get_logs_dir() / "pipeline.log"

    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(str(log_path))
    file_handler.setLevel(log_level)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    return logger