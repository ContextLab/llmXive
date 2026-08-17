import logging
import sys
import json
from pathlib import Path
from typing import Optional

from src.utils.config import get_project_root, ensure_directories

_logger: Optional[logging.Logger] = None

class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs logs as JSON lines."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "timestamp": self.formatTime(record, self.datefmt),
        }
        
        if record.exc_info:
            log_data["exc_info"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)

def setup_logger(name: str = "app", level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return a logger with JSON formatting.
    
    Configures:
    - INFO level logging
    - JSON format for all messages
    - Two handlers:
      1. stdout (console)
      2. data/logs/app.log (file)
    
    Args:
        name: Logger name (default: "app")
        level: Logging level (default: INFO)
    
    Returns:
        Configured logger instance
    """
    global _logger
    
    if _logger is not None and _logger.name == name:
        return _logger

    # Ensure log directory exists
    project_root = get_project_root()
    log_dir = project_root / "data" / "logs"
    ensure_directories([log_dir])
    
    log_file_path = log_dir / "app.log"

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        logger.handlers.clear()

    # Create console handler with JSON formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(JSONFormatter())

    # Create file handler with JSON formatter
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(level)
    file_handler.setFormatter(JSONFormatter())

    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # Add a filter to prevent propagation to root logger if needed
    logger.propagate = False

    _logger = logger
    return logger

def get_log_file() -> Path:
    """
    Return the path to the main application log file.
    
    Returns:
        Path object pointing to data/logs/app.log
    """
    project_root = get_project_root()
    return project_root / "data" / "logs" / "app.log"

def clear_logs() -> None:
    """
    Clear the contents of the log file.
    
    Note: This does not close active file handles in running processes.
    It truncates the file on disk.
    """
    log_path = get_log_file()
    if log_path.exists():
        with open(log_path, "w") as f:
            f.truncate(0)

def log_error(message: str, **kwargs) -> None:
    """
    Log an error message with optional extra context.
    
    Args:
        message: The error message to log
        **kwargs: Additional key-value pairs to include in the log
    """
    logger = setup_logger()
    logger.error(message, extra=kwargs)

def log_warning(message: str, **kwargs) -> None:
    """
    Log a warning message with optional extra context.
    
    Args:
        message: The warning message to log
        **kwargs: Additional key-value pairs to include in the log
    """
    logger = setup_logger()
    logger.warning(message, extra=kwargs)

def log_info(message: str, **kwargs) -> None:
    """
    Log an info message with optional extra context.
    
    Args:
        message: The info message to log
        **kwargs: Additional key-value pairs to include in the log
    """
    logger = setup_logger()
    logger.info(message, extra=kwargs)