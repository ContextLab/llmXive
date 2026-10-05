"""
Structured logging utility for the llmXive pipeline.

Provides a configured logger that writes to stdout and a rotating log file
at logs/pipeline.log. Includes a custom StructuredFormatter for JSON-like
output suitable for parsing by log aggregation systems.
"""

import logging
import sys
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional
import json
import datetime
import traceback


class StructuredFormatter(logging.Formatter):
    """
    A custom formatter that outputs log records as a single-line JSON object.
    Fields include: timestamp, level, logger_name, message, and optional extra fields.
    """

    def format(self, record: logging.LogRecord) -> str:
        # Create a dictionary for the log entry
        log_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }

        # Add any extra fields passed in the record
        if hasattr(record, 'extra_fields') and isinstance(record.extra_fields, dict):
            log_entry.update(record.extra_fields)

        return json.dumps(log_entry)


def get_logger(
    name: str,
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Retrieves or creates a logger with structured output.

    Args:
        name: The name of the logger.
        log_level: The logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Path to the log file. If None, only stdout is used.
        max_bytes: Maximum size of the log file before rotation.
        backup_count: Number of backup log files to keep.

    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Prevent adding handlers multiple times if called repeatedly
    if logger.handlers:
        return logger

    # Formatter for structured output
    formatter = StructuredFormatter()

    # Console Handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler (if log_file is provided)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def main():
    """
    Demonstration of the logger functionality.
    Writes test logs to stdout and logs/pipeline.log.
    """
    # Define the log file path relative to project root
    # Assuming this script runs from the project root or code/
    project_root = Path(__file__).resolve().parent.parent.parent
    log_file_path = project_root / "logs" / "pipeline.log"

    logger = get_logger(
        name="pipeline.demo",
        log_level=logging.DEBUG,
        log_file=str(log_file_path)
    )

    logger.info("Pipeline logger initialized successfully.")
    logger.debug("This is a debug message.")
    logger.warning("This is a warning message.")
    
    try:
        1 / 0
    except ZeroDivisionError:
        logger.error("An error occurred during execution.", exc_info=True)
    
    logger.info("Demo complete. Check logs/pipeline.log for structured output.")


if __name__ == "__main__":
    main()