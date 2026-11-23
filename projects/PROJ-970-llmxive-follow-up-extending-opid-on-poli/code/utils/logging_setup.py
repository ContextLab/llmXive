import logging
import os
import sys
from datetime import datetime
from typing import Optional

LOG_DIR = "logs"

def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    log_format: Optional[str] = None
) -> None:
    """
    Configures the root logger for the project.
    
    Args:
        log_level: The logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional filename to write logs to. If None, logs to console.
        log_format: Optional format string for log messages.
    """
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Ensure log directory exists if file logging is requested
    if log_file:
        os.makedirs(LOG_DIR, exist_ok=True)
        full_log_path = os.path.join(LOG_DIR, log_file)
    else:
        full_log_path = None

    # Configure handlers
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(log_format))
    handlers.append(console_handler)

    # File handler (if specified)
    if full_log_path:
        file_handler = logging.FileHandler(full_log_path)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(file_handler)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers to avoid duplicates
    root_logger.handlers = []
    
    for handler in handlers:
        root_logger.addHandler(handler)

def get_experiment_logger(name: str = "experiment") -> logging.Logger:
    """
    Retrieves or creates a named logger for experiment-specific logging.
    Assumes setup_logging() has been called previously.
    
    Args:
        name: The name of the logger.
        
    Returns:
        A configured Logger instance.
    """
    logger = logging.getLogger(name)
    # Ensure the logger inherits the level from root if not explicitly set
    if logger.level == logging.NOTSET:
        logger.setLevel(logging.INFO)
    return logger
