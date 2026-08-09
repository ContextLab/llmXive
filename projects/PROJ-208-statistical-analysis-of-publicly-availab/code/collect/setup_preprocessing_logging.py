import logging
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs log records as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Include exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Include extra fields if present
        if hasattr(record, "extra_data"):
            log_data["data"] = record.extra_data

        return json.dumps(log_data)


def setup_preprocessing_logging(
    log_path: Optional[Path] = None,
    level: int = logging.INFO,
    name: str = "preprocessing",
) -> logging.Logger:
    """
    Configure a logger for preprocessing tasks that writes JSON-formatted logs.

    Args:
        log_path: Path to the log file. Defaults to data/logs/preprocessing.log
        level: Logging level (e.g., logging.INFO, logging.DEBUG)
        name: Logger name

    Returns:
        Configured logger instance
    """
    if log_path is None:
        log_path = Path("data/logs/preprocessing.log")

    # Ensure directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # File handler with JSON formatting
    file_handler = logging.FileHandler(log_path, mode='w')
    file_handler.setLevel(level)
    file_handler.setFormatter(JSONFormatter())

    # Console handler for immediate feedback (optional, can be disabled)
    # console_handler = logging.StreamHandler(sys.stdout)
    # console_handler.setLevel(logging.WARNING)
    # console_handler.setFormatter(JSONFormatter())

    logger.addHandler(file_handler)
    # logger.addHandler(console_handler)

    return logger


def main() -> None:
    """Entry point for testing the logging setup."""
    logger = setup_preprocessing_logging()
    logger.info("Preprocessing logging initialized successfully.")
    logger.info("This is a test message.")
    logger.warning("This is a test warning.")
    logger.error("This is a test error.")


if __name__ == "__main__":
    main()
