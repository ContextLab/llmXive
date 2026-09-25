import logging
import os
import json
import sys
from datetime import datetime
from typing import Optional, Dict, Any

class JsonFormatter(logging.Formatter):
    """
    A custom logging formatter that outputs log records as structured JSON.
    This ensures pipeline tracing is machine-readable and parseable.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Include exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Include extra fields if present
        if hasattr(record, "extra_data"):
            log_entry.update(record.extra_data)
        
        return json.dumps(log_entry)

def setup_logging(log_file: Optional[str] = None, log_level: int = logging.INFO) -> None:
    """
    Configures the root logger to output structured JSON logs.
    
    Args:
        log_file: Optional path to a log file. If None, logs to stderr.
        log_level: The logging level (e.g., logging.DEBUG, logging.INFO).
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Ensure logs directory exists if file logging is requested
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(JsonFormatter())
        file_handler.setLevel(log_level)
        root_logger.addHandler(file_handler)
    
    # Always add a console handler for immediate visibility
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(JsonFormatter())
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Retrieves a named logger instance.
    
    Args:
        name: The name of the logger (typically __name__).
    
    Returns:
        A configured logger instance.
    """
    return logging.getLogger(name)
