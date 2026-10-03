"""
Logging utility module.
"""
import logging
import logging.config
import os
import yaml
from pathlib import Path
from typing import Optional

def setup_logging(config: dict) -> logging.Logger:
    """
    Setup logging based on configuration.
    
    Args:
        config: Logging configuration dictionary
        
    Returns:
        Configured logger instance
    """
    # Ensure logs directory exists
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Apply logging configuration
    logging.config.dictConfig(config)
    
    return logging.getLogger("ingestion")

def log_timeout(source: str, message: str):
    """Log a timeout event."""
    logger = logging.getLogger("ingestion")
    logger.error(f"TIMEOUT: {source} - {message}")

def log_missing_data(source: str, reason: str):
    """Log missing data event."""
    logger = logging.getLogger("ingestion")
    logger.warning(f"MISSING_DATA: {source} - {reason}")
