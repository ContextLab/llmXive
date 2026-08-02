import logging
import sys
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

# Ensure log directory exists if needed, though typically handled by project setup
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

class LlmXiveError(Exception):
    """Base exception for llmXive pipeline errors."""
    pass

class DataFetchError(LlmXiveError):
    """Raised when data fetching fails."""
    pass

class QuantizationError(LlmXiveError):
    """Raised when quantization fails or produces invalid results."""
    pass

class ModelLoadError(LlmXiveError):
    """Raised when model loading fails."""
    pass

class ResourceLimitExceeded(LlmXiveError):
    """Raised when resource limits (RAM, time) are exceeded."""
    pass

class ConfigurationError(LlmXiveError):
    """Raised when configuration is invalid."""
    pass

class StatisticalAnalysisError(LlmXiveError):
    """Raised when statistical analysis fails."""
    pass

class DegeneracyError(LlmXiveError):
    """Raised when data degeneracy (collapse) is detected."""
    pass

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Configures and returns a logger for the llmXive pipeline.
    
    Args:
        name: The name of the logger module.
    
    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File Handler
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"run_{timestamp}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger

def log_error_and_raise(logger: logging.Logger, error_type: Exception, message: str):
    """
    Logs an error and raises the specified exception.
    
    Args:
        logger: The logger instance.
        error_type: The exception class to raise.
        message: The error message.
    """
    logger.error(message)
    raise error_type(message)

class LogContext:
    """Context manager for adding contextual information to logs."""
    def __init__(self, logger: logging.Logger, context: Dict[str, Any]):
        self.logger = logger
        self.context = context
        self.original_extra = None

    def __enter__(self):
        # In a real implementation, we might use a filter or adapter
        # For now, we just log the context entry
        self.logger.info(f"Entering context: {self.context}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.info(f"Exiting context: {self.context}")
        return False

def log_metric(logger: logging.Logger, name: str, value: float, unit: str = ""):
    """
    Logs a metric in a structured way.
    
    Args:
        logger: The logger instance.
        name: The metric name.
        value: The metric value.
        unit: The unit of the metric.
    """
    formatted_value = f"{value:.6f}" if isinstance(value, float) else str(value)
    unit_str = f" [{unit}]" if unit else ""
    logger.info(f"METRIC: {name} = {formatted_value}{unit_str}")

def validate_config_required(logger: logging.Logger, config: Dict[str, Any], keys: List[str]):
    """
    Validates that required keys exist in a config dictionary.
    
    Args:
        logger: The logger instance.
        config: The configuration dictionary.
        keys: List of required keys.
    
    Raises:
        ConfigurationError: If any required key is missing.
    """
    missing = [k for k in keys if k not in config]
    if missing:
        msg = f"Missing required configuration keys: {missing}"
        log_error_and_raise(logger, ConfigurationError, msg)

def log_resource_snapshot(logger: logging.Logger, snapshot: Dict[str, Any]):
    """
    Logs a snapshot of resource usage (RAM, CPU, etc.).
    
    Args:
        logger: The logger instance.
        snapshot: Dictionary of resource metrics.
    """
    logger.info("RESOURCE SNAPSHOT: " + ", ".join(f"{k}={v}" for k, v in snapshot.items()))
