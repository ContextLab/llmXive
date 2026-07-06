import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        if hasattr(record, 'extra_data'):
            log_record.update(record.extra_data)
        return json.dumps(log_record)

def get_logger(name: str, log_dir: Optional[str] = None) -> logging.Logger:
    """
    Creates a logger that writes to both stdout and a file in the specified directory.
    Uses JSON formatting for structured logs.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    # Create log directory if it doesn't exist
    if log_dir is None:
        log_dir = "data/logs"
    
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # File handler
    file_handler = logging.FileHandler(log_path / f"{name}.log")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(JsonFormatter())

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(JsonFormatter())

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def log_event(event_type: str, data: Dict[str, Any], logger_name: str = "trainer"):
    """
    Logs a structured event to the specified logger.
    """
    logger = get_logger(logger_name)
    record = logger.makeRecord(
        logger.name,
        logging.INFO,
        "",
        0,
        f"Event: {event_type}",
        (),
        None
    )
    record.extra_data = {
        "event_type": event_type,
        **data
    }
    logger.handle(record)