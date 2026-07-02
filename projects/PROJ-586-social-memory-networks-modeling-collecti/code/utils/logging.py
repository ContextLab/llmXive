"""
Logging utilities for the social memory network experiments.
"""
import logging
import os
from pathlib import Path
from typing import Optional

def setup_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with file and console handlers.
    
    Args:
        name: Logger name
        log_file: Path to log file (optional)
        level: Logging level
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log_file provided)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get an existing logger or create a new one."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger = setup_logger(name)
    return logger

def log_experiment_start(logger: logging.Logger, args: dict):
    """Log experiment start with configuration."""
    logger.info("=" * 60)
    logger.info("EXPERIMENT START")
    logger.info("=" * 60)
    for key, value in args.items():
        logger.info(f"  {key}: {value}")
    logger.info("=" * 60)

def log_experiment_end(logger: logging.Logger, results_count: int):
    """Log experiment end with results summary."""
    logger.info("=" * 60)
    logger.info("EXPERIMENT END")
    logger.info(f"Total results: {results_count}")
    logger.info("=" * 60)

def info(logger: logging.Logger, msg: str):
    """Log info message."""
    logger.info(msg)

def warning(logger: logging.Logger, msg: str):
    """Log warning message."""
    logger.warning(msg)

def error(logger: logging.Logger, msg: str):
    """Log error message."""
    logger.error(msg)

def debug(logger: logging.Logger, msg: str):
    """Log debug message."""
    logger.debug(msg)
