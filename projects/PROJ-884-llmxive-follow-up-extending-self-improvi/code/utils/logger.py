"""
Logging utility for the llmXive project.

Provides centralized logging configuration and helper functions.
"""
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Project root path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LOG_DIR = PROJECT_ROOT / "data" / "processed"
LOG_FILE_PATH = LOG_DIR / "experiment.log"

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

def setup_logging(log_file: Optional[Path] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Configure the root logger for the project.
    
    Args:
        log_file: Path to the log file. Defaults to data/processed/experiment.log.
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
    
    Returns:
        The configured root logger.
    """
    if log_file is None:
        log_file = LOG_FILE_PATH
    
    # Ensure parent directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_format)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return root_logger

def log(message: str, level: str = "INFO") -> None:
    """
    Log a message to the configured logger.
    
    Args:
        message: The message to log.
        level: The log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    logger = logging.getLogger("llmXive")
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    log_level = level_map.get(level.upper(), logging.INFO)
    logger.log(log_level, message)

def log_experiment_entry(entry: dict) -> None:
    """
    Log an experiment entry in JSON format.
    
    Args:
        entry: Dictionary containing experiment data.
    """
    import json
    logger = logging.getLogger("llmXive")
    logger.info(json.dumps(entry))

# Initialize logger on module import
setup_logging()
log = logging.getLogger("llmXive").info
log_experiment_entry = log
setup_logging = setup_logging