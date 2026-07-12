"""
Logging utility for llmXive pipeline.
Provides JSON-formatted logging to both file and stdout.
"""
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Ensure the logging directory exists if we are logging to a file
LOG_DIR = Path("code/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs logs as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data)

def setup_logging(
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    name: str = "llmxive"
) -> logging.Logger:
    """
    Configure a logger with JSON formatting for both file and stdout handlers.

    Args:
        log_file: Optional path to a log file. If None, only stdout is used.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        name: Name of the logger.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Create formatters
    json_formatter = JsonFormatter()

    # Console Handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(json_formatter)
    logger.addHandler(console_handler)

    # File Handler (if path provided)
    if log_file:
        file_path = Path(log_file)
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(file_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(json_formatter)
        logger.addHandler(file_handler)

    return logger

def get_logger(name: str = "llmxive") -> logging.Logger:
    """
    Get or create a logger with the specified name.
    Assumes setup_logging has been called or will be called.
    """
    return logging.getLogger(name)

# Convenience function for immediate usage
def init_default_logger() -> logging.Logger:
    """
    Initialize the default logger for the pipeline.
    Logs to code/logs/pipeline.log and stdout.
    """
    log_path = LOG_DIR / "pipeline.log"
    return setup_logging(log_file=str(log_path), level=logging.INFO)

# Example usage / test block
if __name__ == "__main__":
    logger = init_default_logger()
    logger.info("Logger initialized successfully.")
    logger.debug("This is a debug message.")
    logger.warning("This is a warning message.", extra={"extra_data": {"key": "value"}})
    try:
        1 / 0
    except ZeroDivisionError:
        logger.error("An error occurred during execution.", exc_info=True)