import os
import logging
import json
import sys
from datetime import datetime
from typing import Optional, Dict, Any, List
from code.data.paths import get_processed_path, get_results_path, ensure_dir

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    def format(self, record):
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        if record.exc_info:
            log_data["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

def init_logging(log_level: int = logging.INFO) -> None:
    """Initialize the logging system."""
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(log_level)
    ch.setFormatter(StructuredFormatter())
    logger.addHandler(ch)

def get_exclusion_log_path() -> str:
    """Return the path to the exclusion log CSV."""
    return os.path.join(get_processed_path(), "exclusion_log.csv")

def get_error_log_path() -> str:
    """Return the path to the error log JSON."""
    return os.path.join(get_results_path(), "error_log.json")

def log_exclusion(subject_id: str, reason: str, details: str) -> None:
    """Log a subject exclusion event."""
    logging.warning(f"Exclusion: Subject={subject_id}, Reason={reason}, Details={details}")

def log_error(message: str, exception: Optional[Exception] = None) -> None:
    """Log an error event."""
    if exception:
        logging.error(f"{message}: {str(exception)}", exc_info=True)
    else:
        logging.error(message)

def log_warning(message: str) -> None:
    """Log a warning event."""
    logging.warning(message)