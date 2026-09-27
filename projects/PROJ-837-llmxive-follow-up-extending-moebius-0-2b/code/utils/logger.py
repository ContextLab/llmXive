import logging
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

class LlmXiveFormatter(logging.Formatter):
    """Custom formatter for llmXive logs."""
    def format(self, record):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        record.msg = f"[{timestamp}] {record.msg}"
        return super().format(record)

def get_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Get a logger with optional file handler.
    If log_file is provided, logs are written to that file.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(LlmXiveFormatter())
        logger.addHandler(console_handler)

        # File handler (if specified)
        if log_file:
            os.makedirs(os.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(LlmXiveFormatter())
            logger.addHandler(file_handler)

    return logger

def setup_project_logger(name: str) -> logging.Logger:
    """Set up a project-wide logger."""
    log_file = Path("logs") / f"{name}.log"
    return get_logger(name, str(log_file))

def get_console_only_logger(name: str) -> logging.Logger:
    """Get a logger that only logs to console."""
    return get_logger(name, None)

def get_logger_config() -> Dict[str, Any]:
    """Get logger configuration summary."""
    return {
        "level": logging.INFO,
        "handlers": ["console", "file"]
    }

def log_error(message: str, logger_name: str = "root") -> None:
    """Log an error message."""
    logger = get_logger(logger_name)
    logger.error(message)

def log_fatal(message: str, logger_name: str = "root") -> None:
    """Log a fatal message and exit."""
    logger = get_logger(logger_name)
    logger.critical(message)
    sys.exit(1)

# Add the missing datetime import for the log function in annotator.py
# We need to import datetime in the module level or inside the function.
# Since we are adding a new function `log_validation_result` in annotator.py,
# we need to ensure `datetime` is available.
# We will import it inside the function in annotator.py.
# But here, we can also add a utility function to get the current timestamp.
def get_timestamp() -> str:
    """Get current timestamp in the format [YYYY-MM-DD HH:MM:SS]."""
    return f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"
