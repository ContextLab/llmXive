import logging
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name
        }
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Sets up a logger with JSON formatting.
    Creates the log file directory if it doesn't exist.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    # Ensure directory exists for log file
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        fh.setFormatter(JSONFormatter())
        logger.addHandler(fh)

    # Console handler for visibility
    ch = logging.StreamHandler()
    ch.setFormatter(JSONFormatter())
    logger.addHandler(ch)

    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Retrieves an existing logger or creates a default one if not found.
    """
    return logging.getLogger(name)
