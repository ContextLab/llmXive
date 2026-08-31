"""
Base logging infrastructure for the llmXive automated science pipeline.

Provides centralized logging configuration, logger retrieval, and structured
logging utilities to ensure consistent log formatting across the project.
"""
import logging
import sys
from pathlib import Path
from typing import Optional
import json
from datetime import datetime

# Global logger registry to prevent re-initialization
_LOGGERS = {}
_CONFIGURED = False

# Default log format
DEFAULT_FORMAT = (
    "%(asctime)s - %(name)s - %(levelname)s - "
    "[%(filename)s:%(lineno)d] - %(message)s"
)

# Default date format
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Log levels mapping
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    project_root: Optional[Path] = None,
    console: bool = True,
    json_format: bool = False
) -> None:
    """
    Configure the root logger with console and optional file handlers.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file. If None, no file handler is added.
        project_root: Optional project root directory for relative log file paths.
        console: Whether to add a console handler (default: True)
        json_format: Whether to use JSON format for logs (default: False)
    
    Raises:
        ValueError: If log_level is invalid
    """
    global _CONFIGURED
    
    if _CONFIGURED:
        return  # Prevent re-initialization
    
    # Validate log level
    if log_level not in LOG_LEVELS:
        raise ValueError(
            f"Invalid log_level: {log_level}. "
            f"Must be one of: {list(LOG_LEVELS.keys())}"
        )
    
    level = LOG_LEVELS[log_level]
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            fmt=DEFAULT_FORMAT,
            datefmt=DEFAULT_DATE_FORMAT
        )
    
    # Add console handler if requested
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Add file handler if log_file is specified
    if log_file:
        # Resolve relative to project_root if provided
        if project_root and not log_file.is_absolute():
            log_file = project_root / log_file
        
        # Ensure parent directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(str(log_file), mode='a')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    _CONFIGURED = True
    logging.getLogger().info("Logging infrastructure initialized.")

def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger, creating it if necessary.
    
    Args:
        name: Logger name (typically __name__ of the module)
    
    Returns:
        Configured logger instance
    """
    if name in _LOGGERS:
        return _LOGGERS[name]
    
    logger = logging.getLogger(name)
    
    # If logging is not configured yet, set up defaults
    if not _CONFIGURED:
        setup_logging(log_level="INFO")
    
    _LOGGERS[name] = logger
    return logger

class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs as JSON lines.
    Useful for structured logging and log aggregation systems.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry)

def log_with_context(logger: logging.Logger, level: str, message: str, **context) -> None:
    """
    Log a message with additional context fields.
    
    Args:
        logger: Logger instance to use
        level: Log level string (DEBUG, INFO, etc.)
        message: Log message
        **context: Additional key-value pairs to include in log
    """
    if level not in LOG_LEVELS:
        raise ValueError(f"Invalid log level: {level}")
    
    log_record = logger.makeRecord(
        logger.name,
        LOG_LEVELS[level],
        "",
        0,
        message,
        (),
        None
    )
    
    # Attach context as extra fields
    log_record.extra_fields = context
    
    logger.handle(log_record)

def get_logger_for_module(module_name: str) -> logging.Logger:
    """
    Convenience function to get a logger for the current module.
    
    Args:
        module_name: Name of the module (typically __name__)
    
    Returns:
        Configured logger instance
    """
    return get_logger(module_name)
