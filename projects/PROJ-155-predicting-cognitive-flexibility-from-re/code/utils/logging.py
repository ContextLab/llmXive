"""Logging utilities for the pipeline."""
import os
import logging
import csv
from pathlib import Path
from typing import Optional, Dict, Any

from code.data.paths import get_processed_path, ensure_dir

# Global logger instance
_logger = None

def init_logging(level: int = logging.INFO) -> logging.Logger:
    """Initialize logging configuration."""
    global _logger
    
    if _logger is not None:
        return _logger
    
    _logger = logging.getLogger('llmXive')
    _logger.setLevel(level)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    _logger.addHandler(console_handler)
    
    return _logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    if _logger is None:
        init_logging()
    return logging.getLogger(name)

def get_exclusion_log_path() -> Path:
    """Get the path to the exclusion log CSV."""
    return get_processed_path() / "exclusion_log.csv"

def log_exclusion(subject_id: str, reason: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    """Log a subject exclusion to the exclusion log CSV."""
    log_path = get_exclusion_log_path()
    ensure_dir(log_path)
    
    # Extract Mean_FD from metadata if available
    mean_fd = None
    if metadata and isinstance(metadata, dict):
        mean_fd = metadata.get('Mean_FD')
    
    # Check if file exists to determine if we need to write headers
    file_exists = os.path.exists(log_path)
    
    with open(log_path, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Subject_ID', 'Exclusion_Reason', 'Mean_FD'])
        writer.writerow([subject_id, reason, mean_fd if mean_fd is not None else ''])

def log_error(context: str, message: str) -> None:
    """Log an error message."""
    logger = get_logger(__name__)
    logger.error(f"{context}: {message}")

def log_warning(message: str) -> None:
    """Log a warning message."""
    logger = get_logger(__name__)
    logger.warning(message)
