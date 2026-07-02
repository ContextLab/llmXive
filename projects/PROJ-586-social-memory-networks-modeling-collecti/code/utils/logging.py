"""
Logging utilities for the social memory network project.
Configures timestamped logging to experiment.log.
"""
import logging
import os
from pathlib import Path
from typing import Optional

_logger: Optional[logging.Logger] = None

def setup_logger(level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """
    Setup the project logger with timestamps.
    
    Args:
        level: Logging level
        log_file: Optional path to log file (defaults to experiment.log in project root)
    
    Returns:
        Configured logger instance
    """
    global _logger
    
    if _logger is not None:
        return _logger
    
    _logger = logging.getLogger('social_memory')
    _logger.setLevel(level)
    
    # Clear existing handlers
    _logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    _logger.addHandler(console_handler)
    
    # File handler
    if log_file is None:
        # Default to project root
        project_root = Path(__file__).resolve().parent.parent.parent
        log_file = project_root / 'experiment.log'
    else:
        log_file = Path(log_file)
    
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)
    _logger.addHandler(file_handler)
    
    return _logger

def get_logger() -> logging.Logger:
    """Get the project logger instance."""
    global _logger
    if _logger is None:
        return setup_logger()
    return _logger
