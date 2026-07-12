import logging
import sys
import os
from pathlib import Path
from typing import Optional

from config import get_log_level, get_log_format
from utils.error_handlers import ConfigurationError

_logger_instance: Optional[logging.Logger] = None

def setup_logging(log_level: Optional[str] = None, log_format: Optional[str] = None) -> logging.Logger:
    """
    Configure and return the root logger for the pipeline.
    
    Args:
        log_level: Override log level (e.g., 'DEBUG', 'INFO'). If None, uses config.
        log_format: Override log format string. If None, uses config.
        
    Returns:
        The configured root logger.
        
    Raises:
        ConfigurationError: If logging configuration fails.
    """
    global _logger_instance
    
    if _logger_instance is not None:
        return _logger_instance

    try:
        level_str = log_level or get_log_level()
        level = getattr(logging, level_str.upper(), logging.INFO)
        
        fmt_str = log_format or get_log_format()
        if not fmt_str:
            fmt_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        formatter = logging.Formatter(fmt_str)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        
        # File handler for ingestion logs specifically
        # We ensure the data directory exists before attaching a file handler
        # to avoid errors if the project structure isn't fully initialized yet.
        try:
            log_dir = Path("data/logs")
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "ingestion_pipeline.log"
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
        except Exception as e:
            # If we can't write to disk, just log to console but warn
            print(f"Warning: Could not setup file logging: {e}. Logging to console only.")
            file_handler = None

        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        
        # Remove existing handlers to avoid duplicates on repeated calls
        root_logger.handlers.clear()
        root_logger.addHandler(console_handler)
        if file_handler:
            root_logger.addHandler(file_handler)
        
        _logger_instance = root_logger
        return root_logger

    except Exception as e:
        raise ConfigurationError(f"Failed to initialize logging: {e}")

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance, initializing logging if necessary.
    
    Args:
        name: Name of the logger (e.g., 'ingestion.aggregator'). 
              If None, returns the root logger.
              
    Returns:
        A configured logger instance.
    """
    if _logger_instance is None:
        setup_logging()
    
    if name:
        return logging.getLogger(name)
    return _logger_instance
