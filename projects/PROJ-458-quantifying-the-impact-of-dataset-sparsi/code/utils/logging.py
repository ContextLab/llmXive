"""Logging utilities for the research pipeline."""
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs log records as JSON lines."""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            log_entry.update(record.extra_data)
        
        return json.dumps(log_entry)

def get_logger(name: str = "llmXive", log_file: str = None) -> logging.Logger:
    """
    Get a logger instance configured for the project.
    
    Args:
        name: Logger name.
        log_file: Optional path to a JSON log file. If provided, logs are written there.
    
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if logger.handlers:
        return logger
    
    # Console handler (standard output)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)
    
    return logger

def log_result(logger: logging.Logger, message: str, **kwargs):
    """Helper to log a result with extra data."""
    logger.info(message, extra={"extra_data": kwargs})
