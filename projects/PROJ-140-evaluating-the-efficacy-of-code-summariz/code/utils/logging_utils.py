"""
Logging and Error Handling Infrastructure for PROJ-140.

Provides centralized logging configuration, structured loggers, and
an ErrorHandler class to manage exceptions and ensure consistent
error reporting across the pipeline.
"""

import logging
import sys
import os
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Callable
import json

from utils.config_manager import get_config

# Constants for log levels and formats
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_LEVEL = logging.INFO

# Singleton logger instance
_logger_instance: Optional[logging.Logger] = None
_logging_setup_done: bool = False


def setup_logging(log_file: Optional[str] = None, level: int = LOG_LEVEL) -> logging.Logger:
    """
    Configures the root logger and returns the project logger.

    Args:
        log_file: Optional path to a log file. If None, logs to stderr only.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).

    Returns:
        The configured root logger instance.
    """
    global _logger_instance, _logging_setup_done

    if _logging_setup_done and _logger_instance is not None:
        return _logger_instance

    # Load config if available for dynamic settings
    config = get_config()
    if config:
        log_level_str = config.get("logging", {}).get("level", "INFO")
        level = getattr(logging, log_level_str.upper(), logging.INFO)

    # Create project log directory if logging to file
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        # Default log file if none provided
        default_log_dir = Path("data/interaction_logs")
        default_log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = str(default_log_dir / f"pipeline_{timestamp}.log")

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File Handler
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    _logger_instance = root_logger
    _logging_setup_done = True

    # Log initialization
    root_logger.info(f"Logging infrastructure initialized. Log file: {log_file}")
    return root_logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieves a logger instance. Initializes logging if not already done.

    Args:
        name: Name for the logger (e.g., module name). If None, uses root logger.

    Returns:
        A configured logger instance.
    """
    global _logger_instance

    if not _logging_setup_done:
        # Auto-initialize if not explicitly set up
        setup_logging()

    if name is None:
        return _logger_instance if _logger_instance else logging.getLogger()

    return _logger_instance.getChild(name) if _logger_instance else logging.getLogger(name)


class ErrorHandler:
    """
    Centralized error handling utility.

    Provides methods to log exceptions, format error messages,
    and optionally re-raise or swallow exceptions based on context.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initializes the ErrorHandler with a specific logger.

        Args:
            logger: Logger instance to use. Defaults to get_logger().
        """
        self.logger = logger or get_logger("ErrorHandler")

    def handle_exception(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None,
        raise_on_error: bool = False,
        error_code: Optional[str] = None
    ) -> None:
        """
        Logs an exception with detailed context and stack trace.

        Args:
            exception: The exception object to handle.
            context: Optional dictionary of contextual data (e.g., input values, state).
            raise_on_error: If True, re-raises the exception after logging.
            error_code: Optional custom error code for identification.
        """
        error_msg = f"{type(exception).__name__}: {str(exception)}"
        log_level = logging.ERROR

        # Construct structured log message
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "error_code": error_code,
            "exception_type": type(exception).__name__,
            "message": str(exception),
            "context": context or {},
            "traceback": traceback.format_exc()
        }

        # Log the JSON structure for machine parsing if supported, otherwise standard log
        try:
            self.logger.log(log_level, json.dumps(log_data, default=str))
        except (TypeError, ValueError):
            # Fallback if JSON serialization fails
            self.logger.log(log_level, f"Error: {error_msg}")
            self.logger.log(log_level, f"Context: {context}")
            self.logger.log(log_level, f"Traceback:\n{traceback.format_exc()}")

        if raise_on_error:
            raise exception

    def log_error(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ) -> None:
        """
        Logs a manual error message without an exception object.

        Args:
            message: Error message.
            context: Optional context data.
            error_code: Optional error code.
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "error_code": error_code,
            "message": message,
            "context": context or {}
        }
        try:
            self.logger.error(json.dumps(log_data, default=str))
        except (TypeError, ValueError):
            self.logger.error(f"Error: {message}")
            if context:
                self.logger.error(f"Context: {context}")

    def log_warning(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Logs a warning message.

        Args:
            message: Warning message.
            context: Optional context data.
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "context": context or {}
        }
        try:
            self.logger.warning(json.dumps(log_data, default=str))
        except (TypeError, ValueError):
            self.logger.warning(f"Warning: {message}")
            if context:
                self.logger.warning(f"Context: {context}")

    def log_info(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Logs an informational message.

        Args:
            message: Info message.
            context: Optional context data.
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "context": context or {}
        }
        try:
            self.logger.info(json.dumps(log_data, default=str))
        except (TypeError, ValueError):
            self.logger.info(f"Info: {message}")
            if context:
                self.logger.info(f"Context: {context}")


def main():
    """
    Entry point for testing the logging infrastructure.
    Demonstrates setup, logging, and error handling.
    """
    # Initialize logging
    logger = setup_logging()
    logger.info("Logging infrastructure test started.")

    # Test ErrorHandler
    handler = ErrorHandler(logger)

    try:
        # Simulate an error
        raise ValueError("Simulated error for testing")
    except Exception as e:
        handler.handle_exception(e, context={"test_step": "simulation"}, raise_on_error=False)

    handler.log_warning("This is a test warning", context={"source": "main"})
    handler.log_info("Logging test completed successfully.")

    logger.info("Logging infrastructure test finished.")


if __name__ == "__main__":
    main()