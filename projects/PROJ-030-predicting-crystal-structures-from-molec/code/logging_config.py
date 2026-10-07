"""
Logging infrastructure for the llmXive crystal structure prediction pipeline.
Provides structured JSON output to the logs/ directory.
"""
import logging
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from config import get_path_logs, get_project_root


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs log records as structured JSON.
    Includes timestamp, level, logger name, message, and optional extra fields.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
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
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_fields") and isinstance(record.extra_fields, dict):
            log_entry.update(record.extra_fields)

        return json.dumps(log_entry)

    def formatException(self, exc_info: Any) -> str:
        """Format exception information into a string."""
        import traceback
        return "".join(traceback.format_exception(*exc_info))


def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    console_output: bool = True
) -> logging.Logger:
    """
    Configure the root logger with JSON formatting.

    Args:
        log_level: Logging level (default: INFO).
        log_file: Optional path to a log file. If None, logs to the default logs/ directory.
        console_output: Whether to also log to console (default: True).

    Returns:
        The configured root logger.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Determine log file path
    if log_file is None:
        logs_dir = get_path_logs()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = str(logs_dir / f"pipeline_{timestamp}.json")
    else:
        # Ensure the directory exists
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    # File handler with JSON formatter
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)

    # Console handler (optional) with standard formatting for readability
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.

    Args:
        name: Logger name (usually __name__).

    Returns:
        A configured logger instance.
    """
    return logging.getLogger(name)


def log_event(
    logger: logging.Logger,
    event_name: str,
    level: int = logging.INFO,
    **kwargs
) -> None:
    """
    Log a structured event with optional extra fields.

    Args:
        logger: The logger to use.
        event_name: Name of the event (included in the message).
        level: Logging level.
        **kwargs: Additional fields to include in the JSON log entry.
    """
    extra_fields = {"event": event_name, **kwargs}
    record = logger.makeRecord(
        logger.name,
        level,
        "",
        0,
        event_name,
        (),
        None
    )
    record.extra_fields = extra_fields
    logger.handle(record)


def main() -> None:
    """
    Demo function to test the logging setup.
    Writes a sample log entry to verify JSON formatting.
    """
    logger = setup_logging()
    logger.info("Logging infrastructure initialized successfully.")
    log_event(logger, "test_event", message="This is a test log entry", status="success", test_id="T005")
    logger.info("Logging test complete.")


if __name__ == "__main__":
    main()
