"""
Structured logging utility for the llmXive pipeline.

Provides a configured logger that writes to stdout and to a log file
under logs/pipeline.log. Supports standard log levels (DEBUG, INFO,
WARNING, ERROR, CRITICAL) and includes structured formatting.
"""

import logging
import sys
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

# Ensure the logs directory exists
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOGS_DIR / "pipeline.log"

# Custom formatter for structured output
class StructuredFormatter(logging.Formatter):
    """
    A formatter that outputs logs in a structured key=value style
    suitable for parsing and monitoring.
    """
    def format(self, record: logging.LogRecord) -> str:
        # Standard fields
        msg = (
            f"level={record.levelname} "
            f"name={record.name} "
            f"message={record.getMessage()} "
            f"timestamp={record.created} "
            f"module={record.module} "
            f"function={record.funcName} "
            f"line={record.lineno}"
        )
        if record.exc_info:
            msg += f" exception={self.formatException(record.exc_info)}"
        return msg

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieves or creates a logger with the specified name.
    If name is None, returns the root logger configured for the pipeline.

    The logger is configured to:
    - Output to stdout (INFO level and above)
    - Output to logs/pipeline.log (DEBUG level and above, rotating)

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger_name = name if name else "pipeline"
    logger = logging.getLogger(logger_name)

    # Avoid adding handlers multiple times if called repeatedly
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Clear any existing handlers from parent loggers to avoid duplication
    logger.propagate = False

    # Console Handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = StructuredFormatter()
    console_handler.setFormatter(console_formatter)

    # File Handler (logs/pipeline.log) with rotation
    # Max size 10MB, keep 5 backup files
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = StructuredFormatter()
    file_handler.setFormatter(file_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

# Initialize the default pipeline logger immediately
logger = get_logger()

def main():
    """
    Simple test harness to demonstrate logger functionality.
    Runs when the module is executed directly.
    """
    log = get_logger("test_logger")
    log.debug("This is a DEBUG message.")
    log.info("This is an INFO message.")
    log.warning("This is a WARNING message.")
    log.error("This is an ERROR message.")
    log.critical("This is a CRITICAL message.")
    try:
        1 / 0
    except ZeroDivisionError:
        log.exception("An exception occurred during testing.")

    print(f"\nLog file created at: {LOG_FILE.absolute()}")

if __name__ == "__main__":
    main()