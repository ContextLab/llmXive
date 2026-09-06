"""
Logging infrastructure for the llmXive pipeline.

Provides structured JSON logging to `logs/` for pipeline tracing.
Ensures log files are created only if the logs directory exists or can be created.
"""
import logging
import os
import json
import sys
from datetime import datetime
from typing import Optional, Dict, Any

# Ensure logs directory exists
LOGS_DIR = "logs"
os.makedirs(LOGS_DIR, exist_ok=True)

class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data)

def setup_logging(
    logger_name: str = "llmxive",
    log_file: Optional[str] = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Configure and return a logger with JSON formatting.
    
    Args:
        logger_name: Name of the logger.
        log_file: Relative path to log file inside `logs/`. If None, uses default.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
    
    Returns:
        Configured logger instance.
    
    Raises:
        FileNotFoundError: If the logs directory cannot be created.
        PermissionError: If the log file cannot be written.
    """
    # Validate and set log file path
    if log_file is None:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        log_file = f"pipeline_{timestamp}.json"
    
    full_log_path = os.path.join(LOGS_DIR, log_file)
    
    # Ensure directory exists (fail loudly if it can't be created)
    try:
        os.makedirs(LOGS_DIR, exist_ok=True)
    except OSError as e:
        raise FileNotFoundError(f"Cannot create logs directory '{LOGS_DIR}': {e}")
    
    # Get or create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        logger.handlers.clear()
    
    # File handler with JSON formatting
    try:
        file_handler = logging.FileHandler(full_log_path, mode='a', encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(JsonFormatter())
        logger.addHandler(file_handler)
    except PermissionError as e:
        raise PermissionError(f"Cannot write to log file '{full_log_path}': {e}")
    
    # Optional: Console handler for debugging (stderr)
    # Uncomment if console output is desired during development
    # console_handler = logging.StreamHandler(sys.stderr)
    # console_handler.setLevel(logging.DEBUG)
    # console_handler.setFormatter(JsonFormatter())
    # logger.addHandler(console_handler)
    
    return logger

def get_logger(name: str = "llmxive") -> logging.Logger:
    """
    Retrieve an existing logger or create a new one with default config.
    
    This is a convenience function for modules to import and use without
    explicit setup, assuming `setup_logging` has been called once at entry point.
    """
    return logging.getLogger(name)

# Example usage / test entry point
if __name__ == "__main__":
    # Test the logging setup
    log_path = "test_log.json"
    logger = setup_logging(log_file=log_path, level=logging.DEBUG)
    
    logger.info("Pipeline initialization started", extra={"extra_data": {"phase": "setup"}})
    logger.debug("Debug message for verification")
    logger.warning("Warning: Test warning")
    
    try:
        1 / 0
    except ZeroDivisionError:
        logger.exception("An error occurred during test")
    
    print(f"Log file created at: {os.path.join(LOGS_DIR, log_path)}")
    print("Verification: Check the JSON content of the log file.")
