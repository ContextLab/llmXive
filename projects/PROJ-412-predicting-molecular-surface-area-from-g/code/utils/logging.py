import logging
import sys
from pathlib import Path
from typing import Optional
import os
from .config import get_project_root, load_env_config

def setup_logging(log_level: Optional[str] = None) -> logging.Logger:
    """
    Sets up the logging configuration for the project.
    
    Args:
        log_level: Optional log level override. Defaults to env or INFO.
        
    Returns:
        The root logger instance.
    """
    if log_level is None:
        log_level = load_env_config().get("LOG_LEVEL", "INFO")
    
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO

    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger()

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Gets a logger instance with the specified name.
    
    Args:
        name: The name for the logger (usually __name__).
        
    Returns:
        A configured logger instance.
    """
    logger = logging.getLogger(name)
    # Ensure basic config is loaded if not already
    if not logger.handlers:
        setup_logging()
    return logger

def get_logger_level() -> int:
    """
    Gets the current effective log level.
    
    Returns:
        The integer log level constant.
    """
    return logging.getLogger().getEffectiveLevel()
