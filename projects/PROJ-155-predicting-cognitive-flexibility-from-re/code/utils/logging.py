import os
import logging
import json
import sys
from datetime import datetime
from typing import Optional, Dict, Any, List

from code.data.paths import get_processed_path, ensure_dir

class StructuredFormatter(logging.Formatter):
    """
    Custom formatter to output logs as JSON.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        if hasattr(record, 'extra_data'):
            log_entry.update(record.extra_data)
        return json.dumps(log_entry)

def init_logging(log_level: int = logging.INFO) -> logging.Logger:
    """
    Initializes the logger with file and console handlers.
    """
    logger = logging.getLogger('llmXive')
    logger.setLevel(log_level)

    if logger.handlers:
        return logger

    # Ensure log directory exists
    log_dir = os.path.join(get_processed_path(), 'logs')
    ensure_dir(log_dir)
    log_file = os.path.join(log_dir, f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(log_level)
    fh.setFormatter(StructuredFormatter())

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(log_level)
    ch.setFormatter(StructuredFormatter())

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

def get_exclusion_log_path() -> str:
    """
    Returns the path to the exclusion log CSV.
    """
    return os.path.join(get_processed_path(), 'exclusion_log.csv')

def get_error_log_path() -> str:
    """
    Returns the path to the error log file.
    """
    return os.path.join(get_processed_path(), 'logs', 'errors.log')

def log_exclusion(logger: logging.Logger, subject_id: str, reason: str, details: Optional[Dict] = None) -> None:
    """
    Logs an exclusion event.
    """
    extra = {"subject_id": subject_id, "exclusion_reason": reason}
    if details:
        extra.update(details)
    logger.warning("Subject Exclusion", extra={"extra_data": extra})

def log_error(logger: logging.Logger, message: str, details: Optional[Dict] = None) -> None:
    """
    Logs an error event.
    """
    extra = {"error_type": "General"}
    if details:
        extra.update(details)
    logger.error(message, extra={"extra_data": extra})

def log_warning(logger: logging.Logger, message: str, details: Optional[Dict] = None) -> None:
    """
    Logs a warning event.
    """
    extra = {}
    if details:
        extra.update(details)
    logger.warning(message, extra={"extra_data": extra})
