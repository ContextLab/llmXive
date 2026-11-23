"""
Logging and error handling utilities.
"""
import logging
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from config import PathConfig, get_resource_limits

# Custom exceptions
class LlmXiveError(Exception):
    """Base exception for llmXive errors."""
    pass

class ConfigurationError(LlmXiveError):
    """Error related to configuration."""
    pass

class DataLoadError(LlmXiveError):
    """Error related to data loading."""
    pass

class ModelLoadError(LlmXiveError):
    """Error related to model loading."""
    pass

class TrainingError(LlmXiveError):
    """Error related to training."""
    pass

class EvaluationError(LlmXiveError):
    """Error related to evaluation."""
    pass

# Logger registry
_loggers: Dict[str, logging.Logger] = {}

def setup_logging(log_level: int = logging.INFO, log_dir: Optional[Path] = None):
    """
    Setup logging configuration.
    
    Args:
        log_level: Logging level (default: INFO)
        log_dir: Directory for log files (optional)
    """
    if log_dir is None:
        log_dir = PathConfig().logs_dir
    
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler
    log_file = log_dir / "llmxive.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    if name not in _loggers:
        logger = logging.getLogger(name)
        _loggers[name] = logger
    return _loggers[name]

def log_resource_usage():
    """Log current resource usage."""
    limits = get_resource_limits()
    logger = get_logger(__name__)
    logger.info(f"Resource limits: RAM={limits['max_ram_gb']}GB, "
               f"Time={limits['max_time_hours']}h, CPU={limits['cpu_threads']}")

def handle_exception(e: Exception, context: str = ""):
    """
    Handle and log an exception.
    
    Args:
        e: Exception to handle
        context: Additional context information
    """
    logger = get_logger(__name__)
    logger.error(f"{context}: {str(e)}", exc_info=True)
    raise e

# Initialize logging on module import
setup_logging()