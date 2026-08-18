import logging
import json
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# Standardized logging format as per T039c requirement
STANDARD_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

_logger_instance: Optional[logging.Logger] = None

class JsonFormatter(logging.Formatter):
    """Custom formatter for JSON structured logging."""
    def format(self, record):
        log_record = {
            "asctime": self.formatTime(record, self.datefmt),
            "name": record.name,
            "levelname": record.levelname,
            "message": record.getMessage(),
            "pathname": record.pathname,
            "lineno": record.lineno,
        }
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def get_project_root() -> Path:
    """Returns the project root directory (parent of 'code' directory)."""
    current = Path(__file__).resolve()
    # Assuming code/utils/logging_config.py structure
    return current.parent.parent

def setup_logging(
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    use_json: bool = False
) -> None:
    """
    Configures the root logger with the standardized format.
    
    Args:
        log_file: Optional path to a log file. If None, only console logging is configured.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        use_json: If True, uses JSON formatting; otherwise uses the standard string format.
    """
    global _logger_instance
    
    # Configure root logger to avoid duplicate handlers if called multiple times
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers to ensure clean configuration
    if root_logger.handlers:
        root_logger.handlers.clear()

    # Create formatter based on requirements
    if use_json:
        formatter = JsonFormatter()
    else:
        # T039c: Standardize logging format
        formatter = logging.Formatter(STANDARD_FORMAT)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File Handler if requested
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=10*1024*1024, # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Log startup confirmation
    root_logger.info(f"Logging configured with format: {STANDARD_FORMAT}")

def get_logger(name: str) -> logging.Logger:
    """
    Retrieves or creates a named logger.
    
    Args:
        name: The name of the logger (usually __name__).
        
    Returns:
        A configured logging.Logger instance.
    """
    return logging.getLogger(name)

def set_log_level(level: int) -> None:
    """Sets the logging level for the root logger."""
    logging.getLogger().setLevel(level)

def log_with_context(msg: str, context: Optional[dict] = None) -> None:
    """
    Logs a message with optional context dictionary appended to the message.
    
    Args:
        msg: The log message.
        context: Optional dictionary of context to include.
    """
    logger = logging.getLogger(__name__)
    if context:
        ctx_str = ", ".join(f"{k}={v}" for k, v in context.items())
        logger.info(f"{msg} | Context: {ctx_str}")
    else:
        logger.info(msg)
