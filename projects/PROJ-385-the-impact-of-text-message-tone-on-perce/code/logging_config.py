"""
Logging configuration for the research pipeline.

Sets up logging to both console and file.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from config import get_project_root, get_processed_data_dir

def setup_logging(log_file: Optional[Path] = None) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        log_file: Optional path to log file. Defaults to data/pipeline.log.
    
    Returns:
        Root logger instance.
    """
    if log_file is None:
        log_file = get_processed_data_dir() / "pipeline.log"
    
    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to prevent duplicates on re-import
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Log startup message immediately
    root_logger.info("Pipeline logging initialized.")
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Logger instance.
    """
    return logging.getLogger(name)

def log_pipeline_step(step_name: str, logger: Optional[logging.Logger] = None):
    """Log the start of a pipeline step."""
    if logger is None:
        logger = logging.getLogger(__name__)
    logger.info(f"Starting pipeline step: {step_name}")

def log_exclusion(reason: str, record_id: str, logger: Optional[logging.Logger] = None):
    """Log an excluded record."""
    if logger is None:
        logger = logging.getLogger(__name__)
    logger.warning(f"Excluded record {record_id}: {reason}")
