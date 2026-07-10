import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import json
import datetime

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        if record.exc_info:
            log_entry["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a configured logger instance."""
    logger_name = name or __name__
    logger = logging.getLogger(logger_name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(StructuredFormatter())
        logger.addHandler(ch)
        
        # File handler (optional, could be configured via env)
        # For now, just console
    
    return logger

def log_convergence_warning(logger: logging.Logger, message: str, details: Optional[Dict] = None) -> None:
    """Log a convergence warning with optional details."""
    log_entry = {"warning": message}
    if details:
        log_entry.update(details)
    logger.warning(json.dumps(log_entry))

def log_fallback(logger: logging.Logger, fallback_reason: str, original_attempt: str) -> None:
    """Log a fallback event."""
    logger.warning(json.dumps({
        "event": "fallback",
        "reason": fallback_reason,
        "original_attempt": original_attempt
    }))

def log_error_context(logger: logging.Logger, message: str, error: Optional[Exception] = None) -> None:
    """Log an error with context."""
    log_entry = {"error": message}
    if error:
        log_entry["exception_type"] = type(error).__name__
        log_entry["exception_message"] = str(error)
    logger.error(json.dumps(log_entry))
