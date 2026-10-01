"""
Structured logging utility for Socratic Transformers project.

Handles degenerate dialogue events as JSON lines with a strict schema:
{"event_type": str, "timestamp": str, "details": dict}
"""
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure the src package root is in the path if running as script
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


class SocraticJsonFormatter(logging.Formatter):
    """
    Custom formatter that outputs log records as JSON lines.
    Ensures the schema: {"event_type": str, "timestamp": str, "details": dict}
    """

    def format(self, record: logging.LogRecord) -> str:
        # Map standard logging levels to event_type
        event_type = record.levelname.lower()

        # Build the details dict from extra fields and standard attributes
        details: Dict[str, Any] = {
            "message": record.getMessage(),
            "name": record.name,
            "pathname": record.pathname,
            "lineno": record.lineno,
            "funcName": record.funcName,
        }

        # Add any extra fields passed in the log call
        if hasattr(record, "details"):
            if isinstance(record.details, dict):
                details.update(record.details)
            else:
                details["extra_data"] = record.details

        # Ensure timestamp is ISO format with timezone
        timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()

        event_record = {
            "event_type": event_type,
            "timestamp": timestamp,
            "details": details,
        }

        return json.dumps(event_record, default=str)


class SocraticLogger(logging.Logger):
    """
    Custom logger class that uses SocraticJsonFormatter by default.
    """

    def __init__(self, name: str, level: int = logging.NOTSET):
        super().__init__(name, level)
        # Default handler to console if not configured
        if not self.handlers:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(SocraticJsonFormatter())
            self.addHandler(console_handler)

    def log_event(self, event_type: str, message: str, details: Optional[Dict[str, Any]] = None, level: int = logging.INFO) -> None:
        """
        Helper method to log a structured event.
        """
        extra = {"details": details} if details else {}
        self.log(level, message, extra=extra)


# Set the custom logger class
logging.setLoggerClass(SocraticLogger)


def get_logger(name: str) -> SocraticLogger:
    """
    Get or create a logger with the specified name.
    """
    return logging.getLogger(name)


def log_event(
    event_type: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    level: int = logging.INFO,
    logger_name: str = "socratic_logger",
    log_file: Optional[str] = None
) -> None:
    """
    Log an event to the specified logger (and optionally a file).

    Args:
        event_type: The type of event (e.g., 'info', 'error', 'test').
        message: The log message.
        details: Optional dictionary of additional details.
        level: Logging level (default: INFO).
        logger_name: Name of the logger instance.
        log_file: Optional path to a log file. If provided, a file handler
                   with JSON formatting is added.
    """
    logger = get_logger(logger_name)

    # If a file log is requested, add a file handler if it doesn't exist
    if log_file:
        file_handler = None
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler) and handler.filename == str(log_file):
                file_handler = handler
                break

        if file_handler is None:
            file_path = Path(log_file)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(str(file_path))
            file_handler.setFormatter(SocraticJsonFormatter())
            logger.addHandler(file_handler)

    # Log the event
    extra = {"details": details} if details else {}
    logger.log(level, message, extra=extra)


def init_default_logger(log_file: str = "socratic.log") -> None:
    """
    Initialize a default logger that writes to a specific file.
    """
    logger = get_logger("default")
    logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(SocraticJsonFormatter())
    logger.addHandler(file_handler)


def main() -> None:
    """
    Demo function to test the logging utility.
    """
    # Initialize default logger to 'test.log' as per verification requirement
    init_default_logger("test.log")
    logger = get_logger("default")

    # Log a test event
    log_event(
        event_type="test",
        message="Testing the logging utility",
        details={"test_id": 1, "status": "active"},
        log_file="test.log"
    )

    # Log via the logger directly
    logger.log_event("info", "Direct log event", {"source": "main"})

    print("Logging demo complete. Check 'test.log' for output.")


if __name__ == "__main__":
    main()