import logging
import sys
import json
import os
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any

# Global correlation ID for request tracing
_correlation_id = None

class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as JSON for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if _correlation_id:
            log_data["correlation_id"] = _correlation_id
        
        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        return json.dumps(log_data)

class TextFormatter(logging.Formatter):
    """Simple text formatter for console output."""
    def format(self, record: logging.LogRecord) -> str:
        return f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {record.levelname}: {record.getMessage()}"

class CorrelationIdFilter(logging.Filter):
    """Filter to inject correlation ID into log records."""
    def filter(self, record: logging.LogRecord) -> bool:
        if _correlation_id:
            record.correlation_id = _correlation_id
        return True

def get_logger(name: str = "llmXive") -> logging.Logger:
    """Get a configured logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(TextFormatter())
        logger.addHandler(console_handler)
        
        # Add correlation filter
        logger.addFilter(CorrelationIdFilter())
        
    return logger

def configure_logging(log_level: str = "INFO", json_format: bool = False) -> None:
    """Configure global logging settings."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    handler = logging.StreamHandler(sys.stdout)
    if json_format:
        handler.setFormatter(StructuredJsonFormatter())
    else:
        handler.setFormatter(TextFormatter())
        
    root_logger.addHandler(handler)

def set_correlation_id(cid: str) -> None:
    """Set the global correlation ID for request tracing."""
    global _correlation_id
    _correlation_id = cid

def log_with_context(msg: str, level: str = "info", **kwargs) -> None:
    """Log a message with optional extra context."""
    logger = get_logger()
    extra_data = kwargs
    
    record = logger.makeRecord(
        logger.name, getattr(logging, level.upper()), "", 0, msg, (), None
    )
    record.extra_data = extra_data
    logger.handle(record)

# Convenience functions
def info(msg: str, **kwargs):
    log_with_context(msg, "info", **kwargs)

def warning(msg: str, **kwargs):
    log_with_context(msg, "warning", **kwargs)

def error(msg: str, **kwargs):
    log_with_context(msg, "error", **kwargs)

def debug(msg: str, **kwargs):
    log_with_context(msg, "debug", **kwargs)

def critical(msg: str, **kwargs):
    log_with_context(msg, "critical", **kwargs)
