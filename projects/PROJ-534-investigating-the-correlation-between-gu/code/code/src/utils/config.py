"""
Configuration management for the Gut Microbiome - Cognitive Flexibility study.

This module handles:
- Fixed random seeds for reproducibility
- Project path configurations
- Directory creation utilities
"""
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional
import numpy as np
import logging

# ============================================================================
# Project Root and Directory Paths
# ============================================================================

# Determine the project root: the directory containing this config file's parent
# Structure: code/code/src/utils/config.py -> project root is code/code/
_CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = _CURRENT_FILE.parent.parent.parent.parent
CODE_ROOT = PROJECT_ROOT / "code"
SRC_ROOT = CODE_ROOT / "src"

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
RESULTS_DIR = DATA_DIR / "results"

# Logs directory
LOGS_DIR = PROJECT_ROOT / "logs"

# Figures directory
FIGURES_DIR = DATA_DIR / "figures"

# ============================================================================
# Random Seeds for Reproducibility
# ============================================================================

# Fixed seed for all random number generation
SEED = 42

# ============================================================================
# Configuration Dictionary
# ============================================================================

CONFIG: Dict[str, Any] = {
    "seed": SEED,
    "paths": {
        "project_root": str(PROJECT_ROOT),
        "data_dir": str(DATA_DIR),
        "raw_data_dir": str(RAW_DATA_DIR),
        "processed_data_dir": str(PROCESSED_DATA_DIR),
        "results_dir": str(RESULTS_DIR),
        "logs_dir": str(LOGS_DIR),
        "figures_dir": str(FIGURES_DIR),
    },
    "analysis": {
        "alpha_diversity_metrics": ["shannon", "simpson", "chao1"],
        "beta_diversity_metrics": ["bray_curtis", "unifrac_weighted"],
        "correlation_methods": ["pearson", "spearman"],
        "covariates": ["age", "sex", "bmi", "fiber", "antibiotics"],
        "age_cutoff": 65,
        "confidence_level": 0.95,
        "fdr_method": "fdr_bh",  # Benjamini-Hochberg
    },
    "logging": {
        "level": logging.INFO,
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file": str(LOGS_DIR / "pipeline.log"),
    },
}

# ============================================================================
# Helper Functions
# ============================================================================

def get_project_root() -> Path:
    """Return the project root directory."""
    return PROJECT_ROOT

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
    Set the global random seed for reproducibility.
    
    Args:
        seed: The seed value. Defaults to CONFIG['seed'].
    """
    if seed is None:
        seed = SEED
    
    random.seed(seed)
    np.random.seed(seed)
    
    # Log the seed setting
    logger = logging.getLogger(__name__)
    logger.info(f"Global random seed set to {seed}")

def ensure_directories() -> None:
    """
    Create all required directories if they do not exist.
    
    This function ensures the following directories exist:
    - data/raw
    - data/processed
    - data/results
    - data/figures
    - logs
    """
    dirs = [
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        RESULTS_DIR,
        FIGURES_DIR,
        LOGS_DIR,
    ]
    
    logger = logging.getLogger(__name__)
    
    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {directory}")
    
    logger.info("All required directories created/verified.")

def get_config() -> Dict[str, Any]:
    """Return the full configuration dictionary."""
    return CONFIG.copy()

def get_path(key: str) -> Path:
    """
    Retrieve a path from the configuration.
    
    Args:
        key: The path key (e.g., 'raw_data_dir', 'results_dir').
    
    Returns:
        The corresponding Path object.
    
    Raises:
        KeyError: If the key is not found in the paths configuration.
    """
    try:
        path_str = CONFIG["paths"][key]
        return Path(path_str)
    except KeyError:
        raise KeyError(f"Path key '{key}' not found in configuration. Available keys: {list(CONFIG['paths'].keys())}")

# ============================================================================
# Logging Configuration
# ============================================================================

def setup_logging(log_level: int = logging.INFO) -> None:
    """
    Configure the logging system for the project.
    
    Args:
        log_level: The logging level (e.g., logging.DEBUG, logging.INFO).
    """
    # Ensure logs directory exists
    ensure_directories()
    
    log_file = LOGS_DIR / "pipeline.log"
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Avoid duplicate handlers
    if not root_logger.handlers:
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

# ============================================================================
# Module Initialization
# ============================================================================

# Set the global seed when the module is imported
set_global_seed(SEED)