"""
Logging configuration for the LST Wear Prediction pipeline.

This module configures the logging infrastructure to write to logs/pipeline.log
at INFO level. It also provides a utility to raise ValueError when real data
sources are missing, ensuring the pipeline fails loudly rather than falling
back to synthetic data.
"""

import os
import logging
import sys
from pathlib import Path
from typing import Optional

# Ensure the logs directory exists
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "pipeline.log"

# Ensure the directory exists before configuring handlers
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Global logger instance
logger: Optional[logging.Logger] = None

def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    log_format: Optional[str] = None
) -> logging.Logger:
    """
    Configure the root logger for the pipeline.

    Args:
        level: The logging level (default: INFO).
        log_file: Path to the log file (default: logs/pipeline.log).
        log_format: Custom log format string.

    Returns:
        The configured logger instance.
    """
    global logger

    if log_file is None:
        log_file = LOG_FILE
    
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Create logger
    logger = logging.getLogger("llmXive_pipeline")
    logger.setLevel(level)

    # Clear existing handlers to avoid duplicates on re-runs
    logger.handlers.clear()

    # File Handler
    # Ensure parent directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(file_handler)

    # Console Handler (for immediate feedback)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(console_handler)

    return logger

def get_logger() -> logging.Logger:
    """
    Retrieve the configured logger. If not configured, initializes it.

    Returns:
        The logger instance.
    """
    global logger
    if logger is None:
        logger = setup_logging()
    return logger

def raise_on_missing_data(
    source_name: str, 
    source_identifier: str,
    message: Optional[str] = None
) -> None:
    """
    Raise a ValueError indicating that real data is missing.

    This function enforces the 'fail loudly' constraint: if a real data source
    (URL, ID, file) is missing or inaccessible, the pipeline must fail with
    a clear error rather than generating synthetic data.

    Args:
        source_name: Name of the data source (e.g., 'OpenML', 'HuggingFace').
        source_identifier: The specific ID or URL that was not found.
        message: Optional custom error message.

    Raises:
        ValueError: Always raised to halt execution.
    """
    if message is None:
        message = (
            f"CRITICAL DATA MISSING: Real data source '{source_name}' "
            f"with identifier '{source_identifier}' could not be accessed. "
            "The pipeline is configured to FAIL LOUDLY on missing real data. "
            "No synthetic fallback is permitted. Please verify the source "
            "is available and the identifier is correct."
        )
    
    log = get_logger()
    log.error(message)
    raise ValueError(message)

# Initialize logger immediately upon import for immediate use
setup_logging()
logger.info("Logging infrastructure initialized for LST Wear Prediction pipeline.")
