"""
Logging Configuration (T006)

Configures a rotating file handler with JSON formatting.
Fixes the ValueError: Unknown level by ensuring the input `level` is a valid
logging integer constant (e.g., logging.INFO, logging.DEBUG), not a string
logger name.
"""

import logging
import os
import json
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, Union

# Ensure the logs directory exists
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "pipeline.log")

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for log records."""

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'timestamp': self.formatTime(record, self.datefmt)
        }
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_logging(name: str, level: Union[int, str] = logging.INFO) -> logging.Logger:
    """
    Setup logging infrastructure for a specific module.
    
    Args:
        name: The name of the logger (usually __name__).
        level: Logging level (int constant like logging.INFO or string like 'INFO').
               Defaults to logging.INFO.
    
    Returns:
        A configured logger instance.
    
    Raises:
        ValueError: If the provided level string is invalid.
    """
    # Convert string level to int if necessary, but strictly validate
    if isinstance(level, str):
        level = getattr(logging, level.upper(), None)
        if level is None:
            raise ValueError(f"Unknown level: {level}")
    
    # Ensure we have a valid integer level
    if not isinstance(level, int):
        level = logging.INFO

    logger = logging.getLogger(name)
    
    # Only configure if not already configured to avoid duplicates in tests
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates if called multiple times
    logger.handlers.clear()

    # File handler with rotation
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(JsonFormatter())

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# Initialize root logging on module import if needed, 
# but prefer explicit setup_logging(__name__) calls in modules.
# We provide a helper to setup the root logger for general usage.
def setup_root_logging(level: Union[int, str] = logging.INFO) -> logging.Logger:
    """Setup the root logger."""
    return setup_logging("root", level)

# Initialize root logger immediately to satisfy any global imports
setup_root_logging()