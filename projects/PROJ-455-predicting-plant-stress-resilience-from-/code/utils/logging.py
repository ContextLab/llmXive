"""
Logging and error handling infrastructure.
"""
import logging
import json
import os
import sys
from datetime import datetime
from typing import Optional


class DataRejectionError(Exception):
    """Raised when a dataset fails validation criteria."""
    pass


class MissingDataError(Exception):
    """Raised when missing data exceeds the allowed threshold."""
    pass


class JSONFormatter(logging.Formatter):
    """Custom formatter for JSON logging."""
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "extra_data"):
            log_record["data"] = record.extra_data
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


_logger_instance: Optional[logging.Logger] = None


def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Configures and returns a singleton logger with JSON formatting.
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = logging.getLogger(name)
        if _logger_instance.handlers:
            return _logger_instance

        _logger_instance.setLevel(logging.INFO)

        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(JSONFormatter())
        _logger_instance.addHandler(console_handler)

        # File Handler (optional, if logs directory exists)
        log_dir = "data/logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f"{name}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(JSONFormatter())
        _logger_instance.addHandler(file_handler)

    return _logger_instance