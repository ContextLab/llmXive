"""
Basic logging configuration for the research pipeline.
"""
import logging
import sys
from pathlib import Path
from typing import Optional

def setup_logging(log_level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure and return the root logger.
    
    Args:
        log_level: Logging level (default: INFO)
        log_file: Optional path to log file. If None, logs to stderr only.
    
    Returns:
        Configured root logger.
    """
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger