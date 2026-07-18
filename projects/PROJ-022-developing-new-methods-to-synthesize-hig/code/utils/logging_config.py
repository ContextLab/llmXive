"""
Logging configuration for the llmXive automated science pipeline.

Provides structured JSON logging and standardized logger retrieval
across all pipeline stages.
"""
import logging
import json
import sys
from datetime import datetime
from typing import Optional, Dict, Any
import traceback

class StructuredFormatter(logging.Formatter):
    """
    Custom logging formatter that outputs JSON-structured logs.
    
    Includes timestamp, level, logger name, message, and optional
    context data (e.g., task_id, stage, exception info).
    """
    
    def __init__(self, include_stacktrace: bool = True):
        super().__init__()
        self.include_stacktrace = include_stacktrace

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

        # Add extra fields if present
        if hasattr(record, "task_id"):
            log_data["task_id"] = record.task_id
        if hasattr(record, "stage"):
            log_data["stage"] = record.stage
        if hasattr(record, "context"):
            log_data["context"] = record.context

        # Add exception info if present
        if record.exc_info and self.include_stacktrace:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }

        return json.dumps(log_data)

# Global logger registry to avoid re-creating handlers
_loggers: Dict[str, logging.Logger] = {}

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Retrieve or create a named logger with structured formatting.
    
    Args:
        name: Logger name (typically module name)
        level: Logging level threshold
    
    Returns:
        Configured logger instance
    """
    if name not in _loggers:
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Avoid duplicate handlers if called multiple times
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(StructuredFormatter())
            logger.addHandler(handler)
        
        _loggers[name] = logger
    
    return _loggers[name]

def log_event(
    logger: logging.Logger,
    event_type: str,
    message: str,
    level: int = logging.INFO,
    **kwargs: Any
) -> None:
    """
    Log an event with additional context data.
    
    Args:
        logger: Logger instance to use
        event_type: Type of event (e.g., "START", "COMPLETE", "ERROR")
        message: Human-readable message
        level: Logging level
        **kwargs: Additional context fields to attach
    """
    extra = {"event_type": event_type, **kwargs}
    logger.log(level, message, extra=extra)

def setup_pipeline_logger(
    name: str = "pipeline",
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Set up a pipeline logger with optional file output.
    
    Args:
        name: Logger name
        level: Logging level
        log_file: Optional path to write logs to (in addition to stdout)
    
    Returns:
        Configured logger instance
    """
    logger = get_logger(name, level)
    
    if log_file and not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(StructuredFormatter())
        logger.addHandler(file_handler)
    
    return logger