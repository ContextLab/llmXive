import logging
import sys
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import traceback
import json

# Ensure log directory exists if needed, though typically handled by project setup
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

class LlmXiveError(Exception):
    """Base exception for llmXive pipeline errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()

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

    logger.setLevel(logging.DEBUG)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
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

def log_error_and_raise(logger: logging.Logger, error_type: Exception, message: str, details: Optional[Dict[str, Any]] = None):
    """
    Logs an error with full traceback context and raises the specified exception.
    
    Args:
        logger: The logger instance.
        error_type: The exception class to raise.
        message: The error message.
        details: Optional dictionary of contextual details.
    """
    stack_trace = traceback.format_exc() if sys.exc_info()[0] else "No active exception"
    
    log_entry = {
        "level": "ERROR",
        "message": message,
        "stack_trace": stack_trace,
        "details": details,
        "timestamp": datetime.now().isoformat()
    }
    
    logger.error(f"{message} | Details: {details}")
    logger.error(f"Stack Trace:\n{stack_trace}")
    
    raise error_type(message, details=details)

class LogContext:
    """Context manager for adding contextual information to logs."""
    def __init__(self, logger: logging.Logger, context: Dict[str, Any]):
        self.logger = logger
        self.context = context
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"ENTERING CONTEXT: {json.dumps(self.context)}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        status = "SUCCESS" if exc_type is None else f"FAILED ({exc_type.__name__})"
        self.logger.info(f"EXITING CONTEXT: {json.dumps(self.context)} | Status: {status} | Duration: {duration:.2f}s")
        return False

def log_metric(logger: logging.Logger, name: str, value: float, unit: str = "", stage: str = ""):
    """
    Logs a metric in a structured way for easy parsing.
    
    Args:
        logger: The logger instance.
        name: The metric name.
        value: The metric value.
        unit: The unit of the metric.
        stage: Optional stage identifier (e.g., 'quantization', 'training').
    """
    formatted_value = f"{value:.6f}" if isinstance(value, float) else str(value)
    unit_str = f" [{unit}]" if unit else ""
    stage_str = f" [{stage}]" if stage else ""
    msg = f"METRIC{stage_str}: {name} = {formatted_value}{unit_str}"
    logger.info(msg)

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
        log_error_and_raise(logger, ConfigurationError, msg, details={"missing_keys": missing})

def log_resource_snapshot(logger: logging.Logger, snapshot: Dict[str, Any]):
    """
    Logs a snapshot of resource usage (RAM, CPU, etc.) in a structured format.
    
    Args:
        logger: The logger instance.
        snapshot: Dictionary of resource metrics.
    """
    logger.info(f"RESOURCE SNAPSHOT: {json.dumps(snapshot)}")

def log_pipeline_stage(logger: logging.Logger, stage: str, status: str, details: Optional[Dict[str, Any]] = None):
    """
    Logs the start or completion of a pipeline stage.
    
    Args:
        logger: The logger instance.
        stage: Name of the pipeline stage.
        status: 'START', 'COMPLETE', or 'FAIL'.
        details: Optional additional details.
    """
    msg = f"PIPELINE_STAGE: {stage} | STATUS: {status}"
    if details:
        msg += f" | DETAILS: {json.dumps(details)}"
    
    level = logging.INFO if status != "FAIL" else logging.ERROR
    logger.log(level, msg)

def log_exception_details(logger: logging.Logger, exc: Exception, context: str = ""):
    """
    Logs detailed information about an exception.
    
    Args:
        logger: The logger instance.
        exc: The exception instance.
        context: Additional context string.
    """
    exc_type = type(exc).__name__
    exc_msg = str(exc)
    tb_lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
    full_tb = "".join(tb_lines)
    
    log_entry = {
        "context": context,
        "exception_type": exc_type,
        "message": exc_msg,
        "traceback": full_tb
    }
    
    logger.error(f"EXCEPTION: {exc_type} - {exc_msg}")
    logger.error(f"Traceback:\n{full_tb}")
    return log_entry