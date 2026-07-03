"""
Logging infrastructure for the llmXive automated science pipeline.

This module configures a centralized logging system that writes structured logs
to both console and file, with support for different log levels and project-specific
formatting.

Usage:
    from utils.logger import get_logger
    logger = get_logger("my_module")
    logger.info("Processing data...")
"""
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import json
from datetime import datetime
import os

# Project root relative to this file
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_LOG_DIR = _PROJECT_ROOT / "data" / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)

# Default log configuration
_DEFAULT_LOG_LEVEL = logging.INFO
_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Global logger registry to prevent duplicate handlers
_logger_registry: Dict[str, logging.Logger] = {}


class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs logs as JSON lines."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def get_logger(
    name: str,
    log_level: int = _DEFAULT_LOG_LEVEL,
    log_file: Optional[str] = None,
    enable_json: bool = False
) -> logging.Logger:
    """
    Get or create a logger with the specified name.
    
    Args:
        name: Logger name (typically __name__ of the calling module)
        log_level: Logging level (e.g., logging.DEBUG, logging.INFO)
        log_file: Optional custom log file path relative to project root
        enable_json: If True, use JSON formatting for file output
        
    Returns:
        Configured logging.Logger instance
        
    Example:
        >>> from utils.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Starting analysis")
    """
    # Return cached logger if it exists
    if name in _logger_registry:
        logger = _logger_registry[name]
        logger.setLevel(log_level)
        return logger
    
    # Create new logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logger.propagate = False  # Prevent duplicate logs from root handler
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Console handler (always present)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(_LOG_FORMAT, _DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (default to project logs)
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = f"pipeline_{timestamp}.log"
    
    log_path = _LOG_DIR / log_file
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(log_level)
    
    if enable_json:
        file_formatter = JsonFormatter()
    else:
        file_formatter = logging.Formatter(_LOG_FORMAT, _DATE_FORMAT)
    
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Cache the logger
    _logger_registry[name] = logger
    
    return logger


def configure_root_logger(
    log_level: int = _DEFAULT_LOG_LEVEL,
    log_file: Optional[str] = None,
    enable_json: bool = False
) -> None:
    """
    Configure the root logger for the entire application.
    
    This should be called once at application startup to set up
    global logging behavior.
    
    Args:
        log_level: Global logging level
        log_file: Optional custom log file path
        enable_json: Use JSON formatting for file output
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(_LOG_FORMAT, _DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = f"pipeline_{timestamp}.log"
    
    log_path = _LOG_DIR / log_file
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(log_level)
    
    if enable_json:
        file_formatter = JsonFormatter()
    else:
        file_formatter = logging.Formatter(_LOG_FORMAT, _DATE_FORMAT)
    
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)


def log_execution_start(
    task_name: str,
    task_id: str,
    parameters: Optional[Dict[str, Any]] = None
) -> logging.Logger:
    """
    Create a logger and log the start of a task execution.
    
    Args:
        task_name: Name of the task being executed
        task_id: Unique identifier for the task (e.g., "T004")
        parameters: Optional dictionary of task parameters
        
    Returns:
        Configured logger instance for this task
    """
    logger = get_logger(f"task.{task_id}")
    logger.info(f"Task {task_id} ({task_name}) starting")
    
    if parameters:
        logger.info(f"Parameters: {json.dumps(parameters, indent=2, default=str)}")
    
    return logger


def log_execution_end(
    logger: logging.Logger,
    success: bool = True,
    message: Optional[str] = None
) -> None:
    """
    Log the end of a task execution.
    
    Args:
        logger: The logger instance to use
        success: Whether the task completed successfully
        message: Optional status message
    """
    if success:
        logger.info(f"Task completed successfully: {message or 'No errors'}")
    else:
        logger.error(f"Task failed: {message or 'Unknown error'}")