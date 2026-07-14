"""
Logging Infrastructure for the Pipeline.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Union

def get_logger(name: str = __name__) -> logging.Logger:
    """Gets a logger with the specified name."""
    return logging.getLogger(name)

def configure_root_logger(level: int = logging.INFO, log_file: Optional[str] = None) -> None:
    """
    Configures the root logger.
    
    Args:
        level: Logging level (e.g., logging.INFO).
        log_file: Optional path to a log file. If provided, logs are written to file.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

def get_module_logger(module_name: str) -> logging.Logger:
    """Gets a logger for a specific module."""
    return logging.getLogger(module_name)
