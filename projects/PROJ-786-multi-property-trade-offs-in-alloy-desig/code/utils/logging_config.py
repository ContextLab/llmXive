import logging
import json
import sys
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs JSON logs for structured analysis."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "trace_id": getattr(record, 'trace_id', str(uuid.uuid4())),
        }
        
        if hasattr(record, 'context'):
            log_data["context"] = record.context
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)

class ContextFilter(logging.Filter):
    """Filter that injects context into log records."""
    
    def __init__(self, context: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.context = context or {}

    def filter(self, record: logging.LogRecord) -> bool:
        record.context = {**self.context, **getattr(record, 'context', {})}
        return True

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the project's structured configuration."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        configure_root_logger()
    return logger

def configure_root_logger() -> None:
    """Configure the root logger with structured JSON formatting."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(handler)

def log_error_with_context(logger: logging.Logger, message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Log an error message with optional context."""
    extra = {'context': context} if context else {}
    logger.error(message, extra=extra)

def log_warning_with_context(logger: logging.Logger, message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Log a warning message with optional context."""
    extra = {'context': context} if context else {}
    logger.warning(message, extra=extra)

def log_info_with_context(logger: logging.Logger, message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Log an info message with optional context."""
    extra = {'context': context} if context else {}
    logger.info(message, extra=extra)
