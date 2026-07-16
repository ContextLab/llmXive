"""
Structured logging utilities for llmXive pipeline.
Provides JSON-formatted logging suitable for log aggregation and analysis.
"""
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Dict
from utils.config import get_project_root, ensure_dir


# Global logger instance
_logger: Optional[logging.Logger] = None
_handler: Optional[logging.Handler] = None


class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs log records as JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
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
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data)

def get_logger(name: str = "llmxive") -> logging.Logger:
    """
    Get or create a logger with JSON formatting.
    
    Args:
        name: Logger name (default: "llmxive")
        
    Returns:
        Configured logging.Logger instance
    """
    global _logger, _handler

    if _logger is None:
        _logger = logging.getLogger(name)
        _logger.setLevel(logging.INFO)

        # Avoid adding duplicate handlers if called multiple times
        if not _logger.handlers:
            _handler = logging.StreamHandler(sys.stdout)
            _handler.setFormatter(JsonFormatter())
            _logger.addHandler(_handler)

    return _logger

def log_event(
    level: int,
    message: str,
    logger_name: str = "llmxive",
    **extra_fields: Any
) -> None:
    """
    Log an event with structured JSON output.
    
    Args:
        level: Logging level (e.g., logging.INFO, logging.ERROR)
        message: Log message
        logger_name: Name of the logger to use
        **extra_fields: Additional fields to include in the JSON log
    """
    logger = get_logger(logger_name)
    
    # Create a log record with extra data
    record = logger.makeRecord(
        logger.name,
        level,
        "(unknown)",
        0,
        message,
        (),
        None,
    )
    
    if extra_fields:
        record.extra_data = extra_fields
    
    logger.handle(record)

def log_info(message: str, logger_name: str = "llmxive", **extra_fields: Any) -> None:
    """Log an INFO level message."""
    log_event(logging.INFO, message, logger_name, **extra_fields)

def log_warning(message: str, logger_name: str = "llmxive", **extra_fields: Any) -> None:
    """Log a WARNING level message."""
    log_event(logging.WARNING, message, logger_name, **extra_fields)

def log_error(message: str, logger_name: str = "llmxive", **extra_fields: Any) -> None:
    """Log an ERROR level message."""
    log_event(logging.ERROR, message, logger_name, **extra_fields)

def log_debug(message: str, logger_name: str = "llmxive", **extra_fields: Any) -> None:
    """Log a DEBUG level message."""
    log_event(logging.DEBUG, message, logger_name, **extra_fields)

def setup_file_logging(
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    logger_name: str = "llmxive"
) -> Path:
    """
    Configure file logging with JSON formatting.
    
    Args:
        log_file: Path to log file (relative to project root). 
                 If None, uses default path: data/logs/pipeline.log
        level: Logging level
        logger_name: Name of the logger to configure
        
    Returns:
        Path to the created log file
    """
    if log_file is None:
        data_dir = get_project_root() / "data" / "logs"
        ensure_dir(data_dir)
        log_file = str(data_dir / "pipeline.log")
    else:
        log_path = get_project_root() / log_file
        ensure_dir(log_path.parent)
        log_file = str(log_path)

    logger = get_logger(logger_name)
    logger.setLevel(level)

    # Remove existing file handler if present
    existing_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
    for h in existing_handlers:
        logger.removeHandler(h)

    # Add new file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(JsonFormatter())
    file_handler.setLevel(level)
    logger.addHandler(file_handler)

    return Path(log_file)

def reset_logger() -> None:
    """Reset the global logger state (useful for testing)."""
    global _logger, _handler
    if _logger:
        _logger.handlers.clear()
        _logger = None
        _handler = None

# Convenience function to get a configured logger for the current module
def get_module_logger() -> logging.Logger:
    """
    Get a logger configured for the calling module.
    
    Returns:
        Logger instance named after the calling module
    """
    import inspect
    frame = inspect.currentframe()
    if frame and frame.f_back:
        module_name = frame.f_back.f_globals.get("__name__", "llmxive")
        return get_logger(module_name)
    return get_logger()