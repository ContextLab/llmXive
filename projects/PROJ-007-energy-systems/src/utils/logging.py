"""
Logging utilities and reproducibility seed management for the energy systems project.

This module provides:
- Structured JSON logging configuration for the entire pipeline.
- A centralized function to set random seeds for numpy, pandas, and scikit-learn
  to ensure reproducible experimental results.
"""

import logging
import json
import sys
import os
import random
from typing import Optional

import numpy as np
import pandas as pd

# Note: sklearn does not have a single global seed function, but setting the
# global numpy seed and the python random seed covers most initialization paths.
# Specific sklearn estimators also accept a 'random_state' argument.

LOG_DIR = "logs"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    json_format: bool = True
) -> None:
    """
    Configure the root logger with structured output.

    Args:
        log_level: The logging level (e.g., logging.INFO, logging.DEBUG).
        log_file: Optional path to a file for logging. If None, logs to stdout.
        json_format: If True, formats log records as JSON lines. If False, uses standard format.
    """
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates in interactive environments
    logger.handlers.clear()

    # Create formatter
    if json_format:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(LOG_FORMAT)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler if requested
    if log_file:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


class JsonFormatter(logging.Formatter):
    """Formats log records as JSON for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S.%fZ"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_record)


def set_reproducibility_seed(seed: int = 42) -> None:
    """
    Set seeds for all relevant random number generators to ensure reproducibility.

    This function sets:
    - Python's built-in random module
    - NumPy's random state
    - Pandas (relies on NumPy)
    - Note: Scikit-learn estimators must be initialized with random_state=seed individually,
      but this sets the global state for any random operations not explicitly bound to an estimator.

    Args:
        seed: The integer seed value.
    """
    if not isinstance(seed, int):
        raise ValueError(f"Seed must be an integer, got {type(seed)}")

    random.seed(seed)
    np.random.seed(seed)
    
    # Pandas uses numpy internally, so setting numpy's seed covers it.
    # Explicitly setting a seed for pandas is not directly supported as a global function
    # in the same way as numpy, but ensuring numpy is seeded is sufficient for most ops.
    
    # Log the action
    logging.info(f"Reproducibility seed set to: {seed}")
    logging.debug(f"Seed verification - NumPy: {np.random.get_state()[1][0]}, Python: {random.getstate()[1][0]}")