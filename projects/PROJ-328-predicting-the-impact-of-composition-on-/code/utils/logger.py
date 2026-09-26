"""
Logger configuration for the pipeline.
"""

import logging
import json
from pathlib import Path
from typing import Optional
import os
import sys

# Ensure logs directory exists
LOGS_DIR = Path(__file__).parent.parent.parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOGS_DIR / "pipeline.log"


class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs JSON."""

    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        if hasattr(record, 'exc_info') and record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_record)


def get_logger(name: str = __name__) -> logging.Logger:
    """
    Get a logger instance configured for the pipeline.

    Args:
        name: Logger name (usually __name__).

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # File handler with JSON format
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(JsonFormatter())
    logger.addHandler(file_handler)
    
    # Console handler for immediate feedback
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(console_handler)
    
    return logger
