"""
Logging infrastructure setup.
Provides centralized logger configuration and specific logging helpers for
negation exclusions and abort conditions.
"""
import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

from code.config import PROJECT_ROOT

# Log directory
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Sets up a logger with file and console handlers.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    log_filename = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(LOGS_DIR / log_filename)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

def log_negation_exclusion(logger: logging.Logger, comment_id: str, reason: str):
    """
    Logs a comment exclusion due to negation rules.
    """
    logger.warning(f"NEGATION EXCLUSION | ID: {comment_id} | Reason: {reason}")

def log_abort_condition(logger: logging.Logger, reason: str, condition_name: str):
    """
    Logs a critical abort condition.
    """
    logger.critical(f"ABORT CONDITION TRIGGERED: {condition_name}")
    logger.critical(f"Reason: {reason}")

def get_logger(name: str) -> logging.Logger:
    """
    Retrieves an existing logger or creates a new one if not found.
    """
    return logging.getLogger(name)
