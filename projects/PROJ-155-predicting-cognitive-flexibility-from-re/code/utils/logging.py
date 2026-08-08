import os
import logging
import json
import sys
from datetime import datetime
from typing import Optional, Dict, Any, List
from code.config import get_config
from code.data.paths import get_project_root, ensure_dir

class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

def init_logging(log_file: Optional[str] = None) -> None:
    """Initializes the logging system with a structured formatter."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        ensure_dir(os.path.dirname(log_file))
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)

def log_exclusion(subject_id: str, reason: str, details: Optional[Dict] = None) -> None:
    """Logs a subject exclusion event."""
    msg = f"EXCLUSION: Subject {subject_id} excluded due to {reason}."
    if details:
        msg += f" Details: {json.dumps(details)}"
    logging.warning(msg)

def log_error(message: str) -> None:
    """Logs an error message."""
    logging.error(message)

def log_warning(message: str) -> None:
    """Logs a warning message."""
    logging.warning(message)

def get_exclusion_log_path() -> str:
    """Returns the path to the exclusion log file."""
    return os.path.join(get_project_root(), get_config()["data_processed"], "exclusion_log.csv")

def get_error_log_path() -> str:
    """Returns the path to the error log file."""
    return os.path.join(get_project_root(), get_config()["data_processed"], "error_log.json")
