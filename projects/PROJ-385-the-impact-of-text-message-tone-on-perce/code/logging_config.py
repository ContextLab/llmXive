import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from config import get_project_root, get_processed_data_dir

# Global logger instance
_logger: Optional[logging.Logger] = None

def setup_logging(log_file_name: str = "pipeline.log") -> logging.Logger:
    """
    Configure the root logger and project-specific loggers.
    Sets up a file handler for persistent logging of pipeline steps and exclusions,
    and a console handler for immediate feedback.

    Args:
        log_file_name: Name of the log file to create in data/processed/.

    Returns:
        The configured root logger.
    """
    global _logger

    if _logger is not None:
        return _logger

    project_root = get_project_root()
    processed_dir = get_processed_data_dir()
    
    # Ensure log directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    log_path = processed_dir / log_file_name

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Clear existing handlers to avoid duplicates if called multiple times
    if root_logger.handlers:
        root_logger.handlers.clear()

    # Formatter with timestamp, level, and message
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File Handler
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Console Handler (Stream)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    _logger = root_logger
    return _logger

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Retrieve a named logger instance.
    If logging has not been set up yet, it will be initialized automatically.

    Args:
        name: The name of the logger (usually __name__).

    Returns:
        A configured Logger instance.
    """
    if _logger is None:
        setup_logging()
    return logging.getLogger(name)

def log_pipeline_step(step_name: str, details: Optional[str] = None) -> None:
    """
    Log the start or completion of a pipeline step.

    Args:
        step_name: Name of the pipeline step (e.g., "Data Cleaning", "LMM Execution").
        details: Optional additional context about the step.
    """
    logger = get_logger()
    message = f"Pipeline Step: {step_name}"
    if details:
        message += f" | Details: {details}"
    logger.info(message)

def log_exclusion(record_id: str, reason: str, context: Optional[str] = None) -> None:
    """
    Log a specific data exclusion event (e.g., straight-lining, missing data).
    This is critical for auditability and reproducibility.

    Args:
        record_id: The ID of the participant or record being excluded.
        reason: The specific reason for exclusion (e.g., "Zero variance in ratings").
        context: Optional context (e.g., "Detected in 03_clean_data.py").
    """
    logger = get_logger()
    message = f"EXCLUSION | ID: {record_id} | Reason: {reason}"
    if context:
        message += f" | Context: {context}"
    logger.warning(message)