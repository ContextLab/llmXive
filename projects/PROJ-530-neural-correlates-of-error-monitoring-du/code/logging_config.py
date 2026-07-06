"""
Logging configuration and utility functions.
"""
import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_logger_instance = None

def get_logger(name: str = "proj530") -> logging.Logger:
    """
    Get or create a logger instance.
    
    Args:
        name: Name of the logger.
        
    Returns:
        Configured logger instance.
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = logging.getLogger(name)
        if not _logger_instance.handlers:
            _logger_instance.setLevel(logging.INFO)
            
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT, DEFAULT_DATE_FORMAT))
            _logger_instance.addHandler(console_handler)
            
    return logging.getLogger(name)

def initialize_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> None:
    """
    Initialize logging to both console and optionally a file.
    
    Args:
        log_file: Path to log file. If None, only console logging is used.
        level: Logging level.
    """
    logger = get_logger()
    logger.setLevel(level)
    
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Remove existing file handlers to avoid duplicates
        existing_file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        for h in existing_file_handlers:
            logger.removeHandler(h)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT, DEFAULT_DATE_FORMAT))
        file_handler.setLevel(level)
        logger.addHandler(file_handler)

def log_step(step_name: str, logger: Optional[logging.Logger] = None) -> None:
    """
    Log the start of a processing step.
    
    Args:
        step_name: Name of the step.
        logger: Logger instance. If None, uses default.
    """
    if logger is None:
        logger = get_logger()
    logger.info(f"Starting step: {step_name}")

def log_preprocessing_parameter(param_name: str, param_value: str, logger: Optional[logging.Logger] = None) -> None:
    """
    Log a preprocessing parameter setting.
    
    Args:
        param_name: Name of the parameter.
        param_value: Value of the parameter.
        logger: Logger instance.
    """
    if logger is None:
        logger = get_logger()
    logger.info(f"Preprocessing parameter: {param_name} = {param_value}")

def log_artifact(artifact_path: str, artifact_type: str = "file", logger: Optional[logging.Logger] = None) -> None:
    """
    Log the creation of an artifact.
    
    Args:
        artifact_path: Path to the artifact.
        artifact_type: Type of artifact (file, directory, etc.).
        logger: Logger instance.
    """
    if logger is None:
        logger = get_logger()
    logger.info(f"Generated {artifact_type}: {artifact_path}")