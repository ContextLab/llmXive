"""
Structured logging utility for Socratic Transformers project.

Handles degenerate dialogue events as JSON lines following the schema:
{"event_type": str, "timestamp": str, "details": dict}
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure the src directory is in the path for imports when running scripts
# This handles cases where the script is run from the project root or code directory
if "code" in os.getcwd():
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
else:
    # Fallback for relative imports if run from within the code directory structure
    parent = Path(__file__).resolve().parent.parent
    if str(parent) not in sys.path:
        sys.path.insert(0, str(parent))


class SocraticJsonFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.

    Formats log records as JSON lines with the required schema:
    {
      "event_type": str,
      "timestamp": str (ISO 8601),
      "details": dict (contains level, message, extra data)
    }
    """

    def format(self, record: logging.LogRecord) -> str:
        # Create the event structure
        event = {
            "event_type": record.levelname.lower(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": {
                "message": record.getMessage(),
                "logger": record.name,
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }
        }

        # Add any extra fields passed in the log call
        if hasattr(record, "details") and isinstance(record.details, dict):
            event["details"].update(record.details)

        # Handle exception info if present
        if record.exc_info:
            event["details"]["exception"] = self.formatException(record.exc_info)

        return json.dumps(event)


class SocraticLogger:
    """
    Wrapper class to manage structured logging for the project.
    Provides convenient methods for logging events with structured details.
    """

    def __init__(self, name: str, log_file: Optional[Path] = None, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.handlers = []  # Clear existing handlers to avoid duplicates

        # Create console handler with JSON formatter
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(SocraticJsonFormatter())
        self.logger.addHandler(console_handler)

        # Add file handler if log file is specified
        if log_file:
            # Ensure directory exists
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(SocraticJsonFormatter())
            self.logger.addHandler(file_handler)

    def log_event(self, event_type: str, message: str, details: Optional[Dict[str, Any]] = None, level: int = logging.INFO):
        """
        Log a structured event.

        Args:
            event_type: Type of event (e.g., 'dialogue_event', 'critique_generated')
            message: Human-readable message
            details: Additional structured data to include
            level: Logging level (INFO, WARNING, ERROR, etc.)
        """
        extra = {"details": details} if details else {}
        self.logger.log(level, message, extra=extra)

    def info(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.log_event("info", message, details, logging.INFO)

    def warning(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.log_event("warning", message, details, logging.WARNING)

    def error(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.log_event("error", message, details, logging.ERROR)

    def debug(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.log_event("debug", message, details, logging.DEBUG)


# Global logger instance (lazy initialization)
_global_logger: Optional[SocraticLogger] = None


def get_logger(
    name: str = "socratic",
    log_file: Optional[Path] = None,
    level: int = logging.INFO
) -> SocraticLogger:
    """
    Get or create a structured logger instance.

    Args:
        name: Logger name
        log_file: Optional path to log file
        level: Logging level

    Returns:
        SocraticLogger instance
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = SocraticLogger(name, log_file, level)
    return _global_logger


def log_event(
    event_type: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    level: int = logging.INFO,
    logger_name: str = "socratic"
) -> None:
    """
    Convenience function to log a structured event.

    Args:
        event_type: Type of event
        message: Message to log
        details: Additional structured data
        level: Logging level
        logger_name: Name of the logger to use
    """
    logger = get_logger(logger_name)
    logger.log_event(event_type, message, details, level)


def init_default_logger(
    log_dir: Optional[Path] = None,
    level: int = logging.INFO
) -> SocraticLogger:
    """
    Initialize the default logger with optional file output.

    Args:
        log_dir: Directory for log files (default: data/logs)
        level: Logging level

    Returns:
        Initialized SocraticLogger
    """
    if log_dir is None:
        # Default to data/logs relative to project root
        log_dir = Path("data/logs")

    log_file = log_dir / "socratic_events.jsonl"
    return get_logger("socratic", log_file, level)


def main():
    """
    Demo function to test the logging utility.
    """
    # Initialize logger
    logger = init_default_logger()

    # Test logging various events
    logger.info("System initialized", {"version": "1.0.0", "environment": "production"})
    logger.warning("Low memory detected", {"available_mb": 512})
    logger.error("Dialogue generation failed", {"error_code": "E001", "dialogue_id": "dlg_123"})
    logger.debug("Processing step completed", {"step": "critique", "duration_ms": 150})

    # Test direct log_event function
    log_event("dialogue_event", "New dialogue started", {"dialogue_id": "dlg_456", "participants": ["model", "critic"]})

    print("Logging utility test completed. Check data/logs/socratic_events.jsonl for output.")


if __name__ == "__main__":
    main()