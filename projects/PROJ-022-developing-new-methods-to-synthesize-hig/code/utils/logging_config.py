import logging
import json
import sys
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, Union
import os

# Ensure the utils directory is in the path when run as script or module
# This is a safeguard; the runner usually handles path setup.
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Constants for log levels and formats
DEFAULT_LOG_LEVEL = logging.INFO
LOG_FORMAT_STRING = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
JSON_LOG_FORMAT_STRING = "%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(extra_json)s"

class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs log records as JSON lines.
    Includes stack traces for exceptions and structured metadata.
    """
    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        super().__init__(fmt, datefmt)

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": "".join(traceback.format_exception(*record.exc_info))
            }

        # Add extra fields passed via extra={}
        if hasattr(record, 'extra_json'):
            log_data["data"] = record.extra_json

        return json.dumps(log_data)

class TextFormatter(logging.Formatter):
    """
    Standard text formatter for human-readable logs.
    """
    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        super().__init__(fmt or LOG_FORMAT_STRING, datefmt)

def get_logger(name: str, log_level: int = DEFAULT_LOG_LEVEL, 
               output_file: Optional[str] = None, 
               use_json: bool = False) -> logging.Logger:
    """
    Creates and configures a logger with the specified name.
    
    Args:
        name: Name of the logger (usually __name__ of the module).
        log_level: Logging level (e.g., logging.INFO).
        output_file: Optional file path to write logs to.
        use_json: If True, uses StructuredFormatter; otherwise TextFormatter.
    
    Returns:
        Configured Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Determine formatter
    if use_json:
        formatter = StructuredFormatter()
    else:
        formatter = TextFormatter()

    # Console handler (always added)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if output_file:
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
        file_handler = logging.FileHandler(output_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

def log_event(logger: logging.Logger, event_type: str, message: str, 
              data: Optional[Dict[str, Any]] = None, level: int = logging.INFO):
    """
    Helper function to log structured events.
    
    Args:
        logger: The logger instance to use.
        event_type: A string identifier for the type of event (e.g., "PIPELINE_START").
        message: The main log message.
        data: Optional dictionary of additional data to include in the log.
        level: The logging level.
    """
    extra_data = {"event_type": event_type}
    if data:
        extra_data.update(data)
    
    # Pass extra data via the 'extra' dict, mapping to 'extra_json' for the formatter
    logger.log(level, message, extra={"extra_json": extra_data})

def setup_pipeline_logger(name: str = "pipeline", 
                          log_level: int = DEFAULT_LOG_LEVEL,
                          log_dir: str = "data/reports",
                          log_filename: str = "pipeline.log",
                          use_json: bool = True) -> logging.Logger:
    """
    Sets up the main logger for the pipeline stages.
    Ensures the log directory exists and configures both console and file handlers.
    
    Args:
        name: Logger name.
        log_level: Logging level.
        log_dir: Directory to store log files.
        log_filename: Name of the log file.
        use_json: Whether to use JSON formatting.
    
    Returns:
        Configured Logger instance.
    """
    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, log_filename)
    
    return get_logger(name, log_level=log_level, output_file=log_path, use_json=use_json)