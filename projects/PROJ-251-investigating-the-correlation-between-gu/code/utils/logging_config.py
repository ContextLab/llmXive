"""
Logging infrastructure for the llmXive gut microbiome project.

Configures logging to capture exclusion counts, errors, and pipeline progress.
Logs are written to both console (INFO+) and file (DEBUG+).
"""

import logging
import os
from pathlib import Path
from typing import Optional

# Project root relative to this file (code/utils/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_LOG_DIR = _PROJECT_ROOT / "data" / "logs"

# Ensure log directory exists
_LOG_DIR.mkdir(parents=True, exist_ok=True)

# Main logger name
_LOGGER_NAME = "llmXive.gut_microbiome"


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieve or configure the project logger.

    Args:
        name: Optional sub-logger name (e.g., 'ingest', 'correlation').
              If None, returns the root project logger.

    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(_LOGGER_NAME if name is None else f"{_LOGGER_NAME}.{name}")

    # Prevent adding handlers multiple times if called repeatedly
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    # Formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File Handler (DEBUG and above)
    log_file = _LOG_DIR / "pipeline.log"
    try:
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except (OSError, PermissionError) as e:
        # Fallback if file logging fails, but don't crash initialization
        print(f"Warning: Could not create log file {log_file}: {e}")

    # Console Handler (INFO and above)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def log_exclusion_count(category: str, count: int, reason: str, logger_name: Optional[str] = None) -> None:
    """
    Log a specific exclusion event with count and reason.

    This is a helper to standardize logging of filtering/exclusion steps
    required by the pipeline (e.g., T012, T013, T019).

    Args:
        category: The type of data being excluded (e.g., 'subjects', 'taxa').
        count: The number of items excluded.
        reason: The specific reason for exclusion.
        logger_name: Optional sub-logger name.
    """
    logger = get_logger(logger_name)
    if count > 0:
        logger.warning(f"Exclusion: {count} {category} excluded. Reason: {reason}")
    else:
        logger.debug(f"Exclusion check: 0 {category} excluded. Reason: {reason}")


def log_sample_size(n: int, logger_name: Optional[str] = None) -> None:
    """
    Log the final sample size after filtering.

    Args:
        n: The number of subjects in the dataset.
        logger_name: Optional sub-logger name.
    """
    logger = get_logger(logger_name)
    logger.info(f"Sample size validation: N = {n}")


def log_error_context(error: Exception, context: str, logger_name: Optional[str] = None) -> None:
    """
    Log an error with additional context for debugging.

    Args:
        error: The exception instance.
        context: A string describing what was happening when the error occurred.
        logger_name: Optional sub-logger name.
    """
    logger = get_logger(logger_name)
    logger.error(f"Error in {context}: {str(error)}", exc_info=True)