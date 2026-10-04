"""
Logging Configuration (T006)

Configures a rotating file handler with JSON formatting.
"""

import logging
import os
import json
from logging.handlers import RotatingFileHandler
from typing import Any, Dict

from code.config import LOG_FILE

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

def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Setup logging infrastructure.
    Returns the root logger.
    """
    logger = logging.getLogger()
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
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

# Initialize logging on module import
setup_logging()
