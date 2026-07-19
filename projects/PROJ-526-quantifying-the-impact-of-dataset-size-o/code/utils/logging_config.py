import logging
import sys
from pathlib import Path
from typing import Optional

def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Configure logging for the pipeline.
    
    Sets up a root logger that outputs to both stdout and an optional log file.
    Formats include timestamps, log levels, and the module name.
    
    Args:
        log_file: Optional path to a log file. If None, only logs to stdout.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
    
    Returns:
        The configured root logger.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates in repeated calls
    root_logger.handlers.clear()
    
    # Formatter with timestamp, level, name, and message
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        root_logger.addHandler(file_handler)
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: The name of the logger (usually __name__).
    
    Returns:
        A logger instance.
    """
    return logging.getLogger(name)
