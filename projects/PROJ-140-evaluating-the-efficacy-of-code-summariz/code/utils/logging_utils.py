import logging
import sys
import os
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional

# Logger configuration constants
LOG_DIR = Path("data/interaction_logs")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FILE_NAME = "pipeline.log"

_loggers: dict = {}

def setup_logging(log_level: Optional[int] = None) -> logging.Logger:
    """
    Configure the root logger and return it.
    
    Args:
        log_level: Optional logging level (e.g., logging.DEBUG). If None, defaults to INFO.
        
    Returns:
        The configured root logger.
    """
    if log_level is None:
        log_level = logging.INFO

    # Ensure log directory exists
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to prevent duplicates on re-runs
    root_logger.handlers.clear()

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root_logger.addHandler(console_handler)

    # File Handler
    log_file_path = LOG_DIR / LOG_FILE_NAME
    try:
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        root_logger.addHandler(file_handler)
    except (PermissionError, OSError) as e:
        root_logger.warning(f"Could not create file handler for {log_file_path}: {e}")

    return root_logger

def get_logger(name: str) -> logging.Logger:
    """
    Retrieve or create a named logger.
    
    Args:
        name: The name of the logger (usually __name__ of the module).
        
    Returns:
        A configured logger instance.
    """
    if name not in _loggers:
        logger = logging.getLogger(name)
        if not logger.handlers:
            # Inherit level and handlers from root if not explicitly set
            logger.setLevel(logging.getLogger().level)
            # Note: We don't add handlers here to avoid duplication; 
            # root handlers propagate by default unless propagation is disabled.
            # However, for explicit control, we ensure propagation is ON.
            logger.propagate = True
        _loggers[name] = logger
    return _loggers[name]

class ErrorHandler:
    """
    Utility class for centralized error handling and logging.
    """
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or get_logger("ErrorHandler")

    def handle_exception(self, exc: Exception, context: str = "An unexpected error occurred"):
        """
        Log a full exception traceback and re-raise if necessary.
        
        Args:
            exc: The exception instance.
            context: A descriptive string about where the error occurred.
        """
        error_msg = f"{context}: {str(exc)}"
        self.logger.error(error_msg, exc_info=True)
        # Optionally, re-raise or wrap the exception here depending on policy
        # raise exc 

    def log_error(self, message: str, error_code: Optional[str] = None):
        """
        Log an error message with an optional error code.
        
        Args:
            message: The error description.
            error_code: Optional identifier for the error type.
        """
        full_msg = f"[{error_code}] {message}" if error_code else message
        self.logger.error(full_msg)

    def log_warning(self, message: str):
        """Log a warning message."""
        self.logger.warning(message)

    def log_info(self, message: str):
        """Log an informational message."""
        self.logger.info(message)

def main():
    """
    Entry point for testing the logging utility module directly.
    """
    logger = setup_logging(logging.DEBUG)
    test_logger = get_logger("logging_utils.test")
    
    test_logger.info("Logging system initialized successfully.")
    test_logger.debug("This is a debug message.")
    
    handler = ErrorHandler(test_logger)
    try:
        # Simulate an error
        raise ValueError("Simulated test error for logging")
    except Exception as e:
        handler.handle_exception(e, "Test execution block")
    
    test_logger.info("Test execution completed.")

if __name__ == "__main__":
    main()