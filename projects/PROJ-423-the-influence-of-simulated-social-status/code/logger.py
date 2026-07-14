import logging
import json
import os
from datetime import datetime
from typing import Optional

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }
        if record.exc_info:
            log_entry["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

def setup_logger(name: str, log_file: str, level: int = logging.INFO) -> logging.Logger:
    """Sets up a logger with JSON formatting and file output."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times if called repeatedly
    if not logger.handlers:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(JSONFormatter())
        logger.addHandler(fh)
        
        # Optional: Console output for immediate feedback
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
        logger.addHandler(ch)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Gets an existing logger by name."""
    return logging.getLogger(name)
