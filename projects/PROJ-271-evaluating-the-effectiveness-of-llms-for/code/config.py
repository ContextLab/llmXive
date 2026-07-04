"""
Configuration module for the llmXive code smell detection pipeline.

Defines paths, random seeds, batch size constants, and logging configuration.
"""

import logging
import os
from pathlib import Path

# Project Root (assuming this file is at code/config.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directory Paths
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"

# Ensure directories exist
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Random Seeds for reproducibility
RANDOM_SEED = 42
NPY_RANDOM_SEED = 42
TORCH_RANDOM_SEED = 42

# Batch Size Constants
# LLM Batch size constraint: <= 10 (as per FR-004 and task description)
LLM_BATCH_SIZE = 10
MAX_TOTAL_BATCH_SIZE = 50  # Upper bound constraint mentioned in T016

# Dataset Configuration
DATASET_NAME = "codeparrot/github-code"
DATASET_SAMPLE_SIZE = 800

# Model Configuration
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL_PATH = "codellama/CodeLlama-7b-Instruct-GGUF"
LLM_QUANTIZATION_BITS = 4

# Analysis Thresholds
LOC_HIGH_THRESHOLD = 150
LOC_MEDIUM_THRESHOLD = 100
LOC_LOW_THRESHOLD = 50
CYCLOMATIC_HIGH_THRESHOLD = 10

# Logging Configuration Constants
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE_PATH = RESULTS_DIR / "pipeline_metrics.log"

# Statistical Analysis Constants
VIF_THRESHOLD = 5.0
MCNEMAR_ALPHA = 0.05

# Validation Constants
MIN_COMPLETENESS_RATIO = 0.95
MAX_MISSING_ROWS_RATIO = 1.0 - MIN_COMPLETENESS_RATIO


def get_path(relative_path: str) -> Path:
    """
    Resolve a relative path from the project root.

    Args:
        relative_path (str): Path relative to project root.

    Returns:
        Path: Resolved absolute path.
    """
    return PROJECT_ROOT / relative_path


def get_data_path(filename: str) -> Path:
    """
    Resolve a path within the data directory.

    Args:
        filename (str): Filename within the data directory.

    Returns:
        Path: Resolved absolute path.
    """
    return DATA_DIR / filename


def get_processed_path(filename: str) -> Path:
    """
    Resolve a path within the processed data directory.

    Args:
        filename (str): Filename within the processed data directory.

    Returns:
        Path: Resolved absolute path.
    """
    return DATA_PROCESSED_DIR / filename


def get_results_path(filename: str) -> Path:
    """
    Resolve a path within the results directory.

    Args:
        filename (str): Filename within the results directory.

    Returns:
        Path: Resolved absolute path.
    """
    return RESULTS_DIR / filename


def setup_logging() -> logging.Logger:
    """
    Configure and return the root logger with file and console handlers.

    This function implements FR-008 by setting up:
    - A file handler writing to `results/pipeline_metrics.log`
    - A console handler for immediate feedback
    - Specific format and level as defined in constants.

    Returns:
        logging.Logger: The configured root logger.
    """
    logger = logging.getLogger()
    logger.setLevel(LOG_LEVEL)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT)

    # File Handler
    file_handler = logging.FileHandler(LOG_FILE_PATH)
    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(formatter)

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger