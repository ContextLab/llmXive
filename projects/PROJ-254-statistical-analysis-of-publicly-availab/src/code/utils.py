"""
Utility functions for the llmXive music streaming analysis pipeline.

This module provides:
- Deterministic random seed pinning for reproducibility (FR-008).
- Logging setup to write to `pipeline_log.txt` (FR-008).
"""

import logging
import os
import random
import sys
from pathlib import Path

import numpy as np

# Project root is assumed to be the parent of the 'code' directory relative to src
# If run as a script, __file__ points to src/code/utils.py
# We need to go up two levels from src/code to reach the project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_LOG_FILE_PATH = _PROJECT_ROOT / "pipeline_log.txt"


def set_deterministic_seed(seed: int = 42) -> None:
    """
    Pin random seeds for reproducibility across Python, NumPy, and standard libraries.

    Args:
        seed: The integer seed value to use. Default is 42.
    """
    random.seed(seed)
    np.random.seed(seed)
    # If torch or tensorflow were used, they would be seeded here too,
    # but they are not in the current requirements.txt.


def setup_logging(log_file: Path | str | None = None, level: int = logging.INFO) -> logging.Logger:
    """
    Configure the root logger to write to a specific file and stdout.

    Args:
        log_file: Path to the log file. Defaults to `pipeline_log.txt` in the project root.
        level: Logging level (e.g., logging.INFO, logging.DEBUG).

    Returns:
        The configured logger instance.
    """
    if log_file is None:
        log_file = _LOG_FILE_PATH
    else:
        log_file = Path(log_file)

    # Ensure the directory for the log file exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Configure the root logger to avoid duplicate handlers if called multiple times
    logger = logging.getLogger()
    logger.setLevel(level)

    # Remove existing handlers to prevent duplicates on re-runs in same process
    logger.handlers.clear()

    # Create file handler
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(level)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Get a logger instance, ensuring logging is set up.

    Args:
        name: Optional name for the logger. If None, returns the root logger.

    Returns:
        A configured logger instance.
    """
    # Ensure logging is configured at least once
    if not logging.getLogger().handlers:
        setup_logging()
    
    if name:
        return logging.getLogger(name)
    return logging.getLogger()