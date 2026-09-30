"""
Configuration module for the gut microbiome and cognitive flexibility project.

This module defines fixed random seeds for reproducibility and path configurations
for all project directories. It also provides utility functions for setting
global seeds and ensuring directory structures exist.
"""
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional
import numpy as np
import logging
import sys

# Fixed random seed for reproducibility across all random number generators
SEED = 42

# Project root directory (assumes this file is at code/code/src/utils/config.py)
# We traverse up two levels from the current file location
_CURRENT_FILE_PATH = Path(__file__).resolve()
PROJECT_ROOT = _CURRENT_FILE_PATH.parent.parent.parent.parent
CODE_ROOT = _CURRENT_FILE_PATH.parent.parent.parent

# Data directories
DATA_DIR = CODE_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
RESULTS_DIR = DATA_DIR / "results"
FIGURES_DIR = DATA_DIR / "figures"

# Logs directory
LOGS_DIR = CODE_ROOT / "logs"

# Configuration dictionary
CONFIG: Dict[str, Any] = {
    "seed": SEED,
    "paths": {
        "project_root": str(PROJECT_ROOT),
        "code_root": str(CODE_ROOT),
        "data_dir": str(DATA_DIR),
        "raw_data_dir": str(RAW_DATA_DIR),
        "processed_data_dir": str(PROCESSED_DATA_DIR),
        "results_dir": str(RESULTS_DIR),
        "figures_dir": str(FIGURES_DIR),
        "logs_dir": str(LOGS_DIR),
    },
    "analysis": {
        "confidence_level": 0.95,
        "alpha": 0.05,
        "max_skewness_threshold": 1.0,
        "shapiro_wilk_threshold": 0.05,
        "fdr_method": "benjamini_hochberg",
    },
    "covariates": [
        "age",
        "sex",
        "bmi",
        "dietary_fiber",
        "antibiotic_use"
    ],
    "diversity_metrics": {
        "alpha": ["shannon", "simpson", "chao1"],
        "beta": ["bray_curtis", "unifrac_weighted"]
    }
}

def get_project_root() -> Path:
    """Return the project root directory."""
    return PROJECT_ROOT

def get_code_root() -> Path:
    """Return the code root directory."""
    return CODE_ROOT

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
    """Return the results directory."""
    return RESULTS_DIR

def get_logs_dir() -> Path:
    """Return the logs directory."""
    return LOGS_DIR

def get_figures_dir() -> Path:
    """Return the figures directory."""
    return FIGURES_DIR

def set_global_seed(seed: Optional[int] = None) -> None:
    """
    Set the random seed for reproducibility across all libraries.
    
    Args:
        seed: Random seed value. Defaults to CONFIG['seed'] if not provided.
    """
    if seed is None:
        seed = SEED
    
    random.seed(seed)
    np.random.seed(seed)
    
    # Set PYTHONHASHSEED for reproducibility in hash-based operations
    os.environ['PYTHONHASHSEED'] = str(seed)

    logging.info(f"Global random seed set to {seed}")

def ensure_directories() -> None:
    """Create all required directories if they don't exist."""
    directories = [
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        RESULTS_DIR,
        FIGURES_DIR,
        LOGS_DIR
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logging.debug(f"Ensured directory exists: {directory}")

def get_config() -> Dict[str, Any]:
    """Return the full configuration dictionary."""
    return CONFIG.copy()

def get_path(key: str) -> Path:
    """
    Get a path from the configuration by key.
    
    Args:
        key: Configuration key (e.g., 'raw_data_dir', 'results_dir')
    
    Returns:
        Path object for the requested directory
    
    Raises:
        KeyError: If the key is not found in the configuration
    """
    path_keys = {
        "project_root": PROJECT_ROOT,
        "code_root": CODE_ROOT,
        "data_dir": DATA_DIR,
        "raw_data_dir": RAW_DATA_DIR,
        "processed_data_dir": PROCESSED_DATA_DIR,
        "results_dir": RESULTS_DIR,
        "figures_dir": FIGURES_DIR,
        "logs_dir": LOGS_DIR,
    }
    
    if key not in path_keys:
        raise KeyError(f"Path key '{key}' not found in configuration")
    
    return path_keys[key]

def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """
    Configure the root logger to write to the logs directory.
    
    Args:
        log_level: Logging level (default: INFO)
    
    Returns:
        Configured logger instance
    """
    # Ensure logs directory exists
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # File handler
    file_handler = logging.FileHandler(LOGS_DIR / "pipeline.log")
    file_handler.setLevel(log_level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Initialize directories and logging when module is imported
if __name__ == "__main__":
    ensure_directories()
    setup_logging()
    logging.info("Configuration module initialized successfully")
    logging.info(f"Project root: {PROJECT_ROOT}")
    logging.info(f"Data directory: {DATA_DIR}")