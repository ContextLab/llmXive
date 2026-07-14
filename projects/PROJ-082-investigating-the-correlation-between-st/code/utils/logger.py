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
        }
        
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data
        
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)

def get_logger(name: str, log_file: Optional[Path] = None) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        log_file: Optional path to write logs to. If None, logs to stderr.
    
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if logger.handlers:
        return logger
    
    handler: logging.Handler
    if log_file:
        # Ensure directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_file)
    else:
        handler = logging.StreamHandler(sys.stderr)
    
    handler.setFormatter(StructuredFormatter())
    logger.addHandler(handler)
    
    return logger

def log_convergence_warning(logger: logging.Logger, message: str, details: Optional[Dict] = None):
    """Log a convergence warning with optional details."""
    extra = {"details": details} if details else {}
    record = logger.makeRecord(
        logger.name, logging.WARNING, "", 0, message, (), None
    )
    record.extra_data = extra
    logger.handle(record)

def log_fallback(logger: logging.Logger, fallback_reason: str, original_attempt: str):
    """Log that a fallback mechanism was triggered."""
    message = f"Fallback triggered: {fallback_reason} (Original: {original_attempt})"
    extra = {"fallback_reason": fallback_reason, "original_attempt": original_attempt}
    record = logger.makeRecord(
        logger.name, logging.WARNING, "", 0, message, (), None
    )
    record.extra_data = extra
    logger.handle(record)

def log_error_context(logger: logging.Logger, error: Exception, context: Dict[str, Any]):
    """Log an error with additional context."""
    message = f"Error occurred: {str(error)}"
    extra = {"context": context, "error_type": type(error).__name__}
    record = logger.makeRecord(
        logger.name, logging.ERROR, "", 0, message, (), None
    )
    record.extra_data = extra
    logger.handle(record)
