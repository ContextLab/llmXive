import logging
import os
import json
import re
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Tuple

# Ensure the log directory exists
LOG_DIR = Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Constants for rotation as per T008 requirements
MAX_BYTES = 1 * 1024 * 1024  # 1MB
BACKUP_COUNT = 5

# Sensitive keys to scrub from logs
SENSITIVE_KEYS = {"GITHUB_TOKEN", "TOKEN", "API_KEY", "PASSWORD"}

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for log records."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
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

def scrub_sensitive_data(msg: str) -> str:
    """Scrub sensitive data (like tokens) from log messages."""
    scrubbed = msg
    for key in SENSITIVE_KEYS:
        # Match patterns like KEY=value or "KEY": "value"
        # This regex looks for the key followed by optional whitespace, 
        # an equals sign or colon, and then a quoted or unquoted value.
        pattern = rf'({key})[=\s:]*["\']?([A-Za-z0-9_\-]{10,})["\']?'
        scrubbed = re.sub(pattern, rf'\1=***REDACTED***', scrubbed)
    return scrubbed

class SensitiveDataFilter(logging.Filter):
    """Filter to scrub sensitive data from log records before they are formatted."""

    def filter(self, record: logging.LogRecord) -> bool:
        # Scrub the message
        record.msg = scrub_sensitive_data(record.msg)
        # Scrub args if they are strings (simple case)
        if record.args:
            if isinstance(record.args, tuple):
                record.args = tuple(
                    scrub_sensitive_data(str(arg)) if isinstance(arg, str) else arg
                    for arg in record.args
                )
            elif isinstance(record.args, dict):
                record.args = {
                    k: scrub_sensitive_data(str(v)) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
        return True

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Configure and return a logger with JSON formatting,
    TimedRotatingFileHandler, and sensitive data scrubbing.
    
    The handler is configured with:
    - maxBytes=1MB
    - backupCount=5
    - Output to data/logs/
    """
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times if called repeatedly
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # Create file handler with TimedRotatingFileHandler as required
    log_file = LOG_DIR / f"{name}.log"
    
    # Configure TimedRotatingFileHandler with specific rotation parameters
    file_handler = TimedRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        backupCount=BACKUP_COUNT,
        encoding="utf-8"
    )
    
    # Set the level and formatter
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(JSONFormatter())
    
    # Add the sensitive data filter
    file_handler.addFilter(SensitiveDataFilter())

    # Create console handler for visibility during development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(JSONFormatter())
    console_handler.addFilter(SensitiveDataFilter())

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def setup_logging(name: str = "llmXive") -> logging.Logger:
    """
    Convenience function to setup and return the logger.
    Matches the interface expected by other modules (e.g., 00_validate_structure.py).
    """
    return get_logger(name)

# Helper function to validate log configuration
def validate_logging_config() -> Tuple[bool, str]:
    """
    Validates that the logging configuration meets T008 requirements.
    Returns (is_valid, message).
    """
    try:
        logger = get_logger("validation_test")
        if not logger.handlers:
            return False, "No handlers configured"
        
        file_handler = None
        for handler in logger.handlers:
            if isinstance(handler, TimedRotatingFileHandler):
                file_handler = handler
                break
        
        if not file_handler:
            return False, "TimedRotatingFileHandler not found"
        
        # Check backupCount (maxBytes is not directly exposed on the handler object 
        # in a simple way, but we can check the class attributes or doc)
        if file_handler.backupCount != BACKUP_COUNT:
            return False, f"backupCount mismatch: expected {BACKUP_COUNT}, got {file_handler.backupCount}"
        
        # Check that the log directory exists
        if not LOG_DIR.exists():
            return False, f"Log directory {LOG_DIR} does not exist"
        
        # Check that the log file path is under data/logs
        if not str(file_handler.baseFilename).startswith(str(LOG_DIR)):
            return False, f"Log file path {file_handler.baseFilename} is not under {LOG_DIR}"
        
        return True, "Logging configuration is valid"
    except Exception as e:
        return False, f"Validation failed with exception: {str(e)}"