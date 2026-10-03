"""
Logger configuration for the pipeline.

Provides a centralized logging utility that writes JSON-formatted logs
to a file and human-readable logs to the console.
"""

import logging
import json
from pathlib import Path
from typing import Optional
import os
import sys

# Ensure logs directory exists relative to project root
# Assuming code/utils/ -> code/ -> project_root
PROJECT_ROOT = Path(__file__).parent.parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOGS_DIR / "pipeline.log"

# Ensure directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)


class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs log records as JSON strings."""

    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        if hasattr(record, 'exc_info') and record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        
        if hasattr(record, 'extra_data'):
            log_record.update(record.extra_data)
        
        return json.dumps(log_record)


def get_logger(name: str = "pipeline") -> logging.Logger:
    """
    Get a logger instance configured for the pipeline.

    Args:
        name: Logger name (defaults to 'pipeline' or __name__ if called from module).

    Returns:
        Configured logger instance with file and console handlers.
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times if called repeatedly
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # File handler with JSON format
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(JsonFormatter(datefmt="%Y-%m-%dT%H:%M:%S"))
    logger.addHandler(file_handler)
    
    # Console handler for immediate feedback (human-readable)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt="%Y-%m-%dT%H:%M:%S"
    ))
    logger.addHandler(console_handler)
    
    return logger
