"""
Code package for the Molecular Complexity vs Degradation study.

This package provides the core logic for:
- Ingesting pharmaceutical data
- Calculating molecular descriptors
- Performing statistical analysis
- Generating visualizations and reports
"""

import logging
import sys
from pathlib import Path

# Configure package-level logging
def setup_logger(name: str, log_file: str | None = None, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with console and optional file output.
    
    Args:
        name: Logger name (usually __name__)
        log_file: Optional path to log file
        level: Logging level (default: INFO)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding duplicate handlers if logger already exists
    if logger.handlers:
        return logger
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Initialize default logger for the package
logger = setup_logger(__name__, log_file="data/logs/pipeline.log")