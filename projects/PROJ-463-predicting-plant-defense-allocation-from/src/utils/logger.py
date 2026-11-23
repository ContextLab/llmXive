"""
Logging configuration and utility functions for the plant defense allocation pipeline.

This module provides a centralized logging setup that ensures consistent log formatting,
file rotation, and log level management across the entire pipeline.
"""

import logging
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Constants
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_DIR = "data/logs"

class PipelineLogger:
    """
    A wrapper around Python's logging module that provides pipeline-specific
    logging functionality.
    """
    
    _instance: Optional['PipelineLogger'] = None
    _logger: Optional[logging.Logger] = None
    
    def __new__(cls, *args, **kwargs):
        """Ensure singleton pattern for the logger instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, log_dir: Optional[str] = None, log_level: int = DEFAULT_LOG_LEVEL):
        """
        Initialize the PipelineLogger.
        
        Args:
            log_dir: Directory to store log files. Defaults to DEFAULT_LOG_DIR.
            log_level: Logging level (e.g., logging.DEBUG, logging.INFO).
        """
        if self._logger is not None:
            return  # Already initialized
        
        self.log_dir = Path(log_dir) if log_dir else Path(DEFAULT_LOG_DIR)
        self.log_level = log_level
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure the logging system."""
        # Create log directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a logger
        self._logger = logging.getLogger("plant_defense_pipeline")
        self._logger.setLevel(self.log_level)
        
        # Prevent adding handlers multiple times
        if self._logger.handlers:
            return
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        console_formatter = logging.Formatter(DEFAULT_LOG_FORMAT, DEFAULT_DATE_FORMAT)
        console_handler.setFormatter(console_formatter)
        
        # Create file handler with rotation
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"pipeline_{timestamp}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(console_formatter)
        
        # Add handlers to logger
        self._logger.addHandler(console_handler)
        self._logger.addHandler(file_handler)
        
        # Log initialization
        self._logger.info(f"Logging initialized. Log file: {log_file}")
    
    def get_logger(self) -> logging.Logger:
        """Get the underlying logger instance."""
        return self._logger
    
    def info(self, message: str):
        """Log an info message."""
        self._logger.info(message)
    
    def debug(self, message: str):
        """Log a debug message."""
        self._logger.debug(message)
    
    def warning(self, message: str):
        """Log a warning message."""
        self._logger.warning(message)
    
    def error(self, message: str):
        """Log an error message."""
        self._logger.error(message)
    
    def critical(self, message: str):
        """Log a critical message."""
        self._logger.critical(message)
    
    def exception(self, message: str):
        """Log an exception message with traceback."""
        self._logger.exception(message)
    
    def get_log_file(self) -> Path:
        """Get the path to the current log file."""
        return self.log_file if hasattr(self, 'log_file') else self.log_dir / "pipeline.log"

def setup_logging(log_dir: Optional[str] = None, log_level: int = DEFAULT_LOG_LEVEL) -> PipelineLogger:
    """
    Setup and return the pipeline logger instance.
    
    Args:
        log_dir: Directory to store log files.
        log_level: Logging level.
        
    Returns:
        PipelineLogger instance.
    """
    return PipelineLogger(log_dir=log_dir, log_level=log_level)

def set_log_level(level: int):
    """
    Set the logging level for the pipeline logger.
    
    Args:
        level: The new logging level.
    """
    logger = PipelineLogger()
    logger._logger.setLevel(level)
    for handler in logger._logger.handlers:
        handler.setLevel(level)

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance, optionally with a specific name.
    
    Args:
        name: Optional name for the logger. If None, returns the main pipeline logger.
        
    Returns:
        logging.Logger instance.
    """
    if name is None:
        return PipelineLogger().get_logger()
    else:
        return logging.getLogger(f"plant_defense_pipeline.{name}")
