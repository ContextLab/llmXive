import logging
import os
import json
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Dict, Any

LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        return json.dumps(log_data)

def get_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """Get a logger with JSON formatting and rotating file handler."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File Handler
    if log_file is None:
        log_file = "pipeline.log"
    
    file_path = LOG_DIR / log_file
    file_handler = RotatingFileHandler(file_path, maxBytes=5*1024*1024, backupCount=3)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JsonFormatter())
    logger.addHandler(file_handler)

    return logger

def log_with_extra(logger: logging.Logger, level: int, msg: str, extra: Dict[str, Any]):
    """Log a message with extra JSON data."""
    record = logger.makeRecord(logger.name, level, "", 0, msg, (), None)
    record.extra_data = extra
    logger.handle(record)
