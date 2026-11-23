import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

# Define the log format string as specified in the task
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Global logger instance to be used across the pipeline
_logger: Optional[logging.Logger] = None

def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Configure the logging infrastructure for the pipeline.

    Sets up a logger with the following handlers:
    1. Console handler (stdout)
    2. Rotating file handler writing to 'logs/pipeline.log' (or a custom path)

    Args:
        log_file: Optional path to the log file. Defaults to 'logs/pipeline.log' relative to project root.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).

    Returns:
        The configured root logger.
    """
    global _logger

    # Determine project root (assuming standard structure: code/src/utils -> code/)
    # We look for 'logs' directory relative to the project root.
    # Based on T001, logs are likely at project root or 'data' structure.
    # Task specifies: output to 'logs/pipeline.log'.
    if log_file is None:
        # Assume project root is the parent of 'code' directory
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent
        log_dir = project_root / "logs"
        log_file = log_dir / "pipeline.log"

    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create or get the root logger
    logger = logging.getLogger("llmXive_pipeline")
    logger.setLevel(level)

    # Clear existing handlers to avoid duplicates on re-calls
    if logger.handlers:
        logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler (Rotating)
    # Max size 10MB, keep 5 backup files
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    _logger = logger
    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieve the configured logger.

    Args:
        name: Optional name for a child logger (e.g., 'llmXive_pipeline.data').
              If None, returns the main pipeline logger.

    Returns:
        A configured logger instance.
    """
    global _logger
    if _logger is None:
        # If setup_logging hasn't been called yet, initialize with defaults
        _logger = setup_logging()

    if name:
        return _logger.getChild(name)
    return _logger

def log_subject_exclusion(subject_id: str, reason: str, logger: Optional[logging.Logger] = None):
    """
    Log the exclusion of a subject with a specific reason.

    Args:
        subject_id: The ID of the subject being excluded.
        reason: The reason for exclusion (e.g., "High motion: FD=0.25").
        logger: Optional logger instance.
    """
    log_msg = f"Subject excluded: {subject_id} - Reason: {reason}"
    if logger:
        logger.warning(log_msg)
    else:
        get_logger().warning(log_msg)

def log_processing_step(step_name: str, details: Optional[str] = None, logger: Optional[logging.Logger] = None):
    """
    Log the start or completion of a processing step.

    Args:
        step_name: Name of the processing step.
        details: Optional additional details about the step.
        logger: Optional logger instance.
    """
    if details:
        log_msg = f"Step '{step_name}' - {details}"
    else:
        log_msg = f"Step '{step_name}' started"

    if logger:
        logger.info(log_msg)
    else:
        get_logger().info(log_msg)

def main():
    """
    Main entry point for testing the logging configuration standalone.
    """
    # Initialize logging
    logger = setup_logging()

    # Test logging levels
    logger.debug("This is a debug message.")
    logger.info("This is an info message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")

    # Test child logger
    child_logger = get_logger("data.download")
    child_logger.info("Data download module initialized.")

    # Test utility functions
    log_processing_step("Data Validation")
    log_subject_exclusion("101010", "Mean FD >= 0.2mm")

    print("Logging configuration test completed. Check 'logs/pipeline.log' and console.")

if __name__ == "__main__":
    main()