"""
Structured logging infrastructure for the alloy design pipeline.

Provides centralized configuration for JSON-formatted logs with
correlation IDs, severity levels, and structured context.
"""
import logging
import json
import sys
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

# Default log format configuration
DEFAULT_LOG_LEVEL = "INFO"
LOG_FILE_DIR = Path("data/logs")
LOG_FILE_PATTERN = "pipeline_{date}.jsonl"

# Global logger registry
_loggers: Dict[str, logging.Logger] = {}
_configured = False


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs as JSON lines (JSONL).
    Includes correlation IDs, timestamps, and custom context fields.
    """
    
    def __init__(self, service_name: str = "alloy-pipeline"):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        # Ensure extra fields exist
        if not hasattr(record, "extra_data"):
            record.extra_data = {}

        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": self.service_name,
            "correlation_id": getattr(record, "correlation_id", None),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
            "context": record.extra_data,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


class ContextFilter(logging.Filter):
    """
    Filter that injects correlation IDs and global context into log records.
    """
    
    def __init__(self, correlation_id: Optional[str] = None):
        super().__init__()
        self.correlation_id = correlation_id or str(uuid.uuid4())

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "correlation_id"):
            record.correlation_id = self.correlation_id
        if not hasattr(record, "extra_data"):
            record.extra_data = {}
        return True


def get_logger(name: str, correlation_id: Optional[str] = None) -> logging.Logger:
    """
    Retrieves or creates a named logger with structured formatting.
    
    Args:
        name: Logger name (typically __name__ of the calling module)
        correlation_id: Optional ID to track requests across modules
        
    Returns:
        Configured logger instance
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Capture all, filter at handler level

    # Add context filter
    context_filter = ContextFilter(correlation_id)
    logger.addFilter(context_filter)

    # Console handler (JSON)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(StructuredFormatter())
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    # File handler (JSONL)
    LOG_FILE_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    log_file = LOG_FILE_DIR / LOG_FILE_PATTERN.format(date=date_str)
    
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setFormatter(StructuredFormatter())
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    _loggers[name] = logger
    return logger


def configure_root_logger(level: str = DEFAULT_LOG_LEVEL, service_name: str = "alloy-pipeline") -> None:
    """
    Configures the root logger with structured formatting.
    Must be called once at application startup.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        service_name: Name to include in log entries
    """
    global _configured
    if _configured:
        return

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(StructuredFormatter(service_name))
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    # File handler
    LOG_FILE_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    log_file = LOG_FILE_DIR / LOG_FILE_PATTERN.format(date=date_str)
    
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setFormatter(StructuredFormatter(service_name))
    file_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)

    _configured = True


def log_error_with_context(
    logger: logging.Logger,
    message: str,
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None
) -> None:
    """
    Logs an error with structured context and exception details.
    
    Args:
        logger: Logger instance
        message: Error message
        error: Exception object
        context: Additional context dictionary
        correlation_id: Optional correlation ID
    """
    extra = context or {}
    extra["error_type"] = type(error).__name__
    extra["error_message"] = str(error)
    
    logger.error(
        message,
        exc_info=True,
        extra={"extra_data": extra, "correlation_id": correlation_id}
    )


def log_warning_with_context(
    logger: logging.Logger,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None
) -> None:
    """
    Logs a warning with structured context.
    
    Args:
        logger: Logger instance
        message: Warning message
        context: Additional context dictionary
        correlation_id: Optional correlation ID
    """
    extra = context or {}
    logger.warning(
        message,
        extra={"extra_data": extra, "correlation_id": correlation_id}
    )


def log_info_with_context(
    logger: logging.Logger,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None
) -> None:
    """
    Logs an info message with structured context.
    
    Args:
        logger: Logger instance
        message: Info message
        context: Additional context dictionary
        correlation_id: Optional correlation ID
    """
    extra = context or {}
    logger.info(
        message,
        extra={"extra_data": extra, "correlation_id": correlation_id}
    )
