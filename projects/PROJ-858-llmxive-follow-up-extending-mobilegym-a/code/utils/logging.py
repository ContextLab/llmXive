import json
import logging
import os
import sys
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Custom Exceptions
class LlmXiveError(Exception):
    """Base exception for LLMXive pipeline errors."""
    pass

class ConfigurationError(LlmXiveError):
    """Raised when configuration is invalid or missing."""
    pass

class DataError(LlmXiveError):
    """Raised when data loading or processing fails."""
    pass

class SchedulerError(LlmXiveError):
    """Raised when scheduler logic fails."""
    pass

class CoverageError(LlmXiveError):
    """Raised when coverage vector operations fail."""
    pass

class JSONFormatter(logging.Formatter):
    """Custom formatter to output logs as JSON."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra context if present
        if hasattr(record, 'context'):
            log_entry["context"] = record.context
        
        return json.dumps(log_entry)

def get_logger(name: str = "llmxive") -> logging.Logger:
    """
    Configures and returns a logger with JSON formatting.
    """
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)
    
    return logger

def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Logs a message with optional structured context.
    """
    extra = {"context": context} if context else {}
    logger.log(level, message, extra=extra)

def log_error(logger: logging.Logger, error: Exception, message: str = "An error occurred") -> None:
    """
    Logs an error with exception details.
    """
    log_with_context(
        logger,
        logging.ERROR,
        message,
        context={
            "exception_type": type(error).__name__,
            "exception_message": str(error)
        }
    )

def configure_logging(log_file: Optional[str] = None) -> None:
    """
    Configures global logging to also write to a file if specified.
    """
    if log_file:
        logger = logging.getLogger("llmxive")
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)
