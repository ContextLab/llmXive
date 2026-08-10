import logging
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from utils.config import get_config, get_path


class JSONFormatter(logging.Formatter):
    """
    Custom logging formatter that outputs log records as JSON lines.
    This ensures that log entries can be easily parsed for analysis
    and debugging, specifically for tracking excluded issues.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
        }

        # Include exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Include extra context if provided in record
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data

        return json.dumps(log_entry)


def setup_preprocessing_logging(log_path: Optional[Path] = None) -> logging.Logger:
    """
    Configures and returns a logger specifically for preprocessing tasks.
    This logger writes JSON-formatted logs to a file and also outputs
    to the console for immediate visibility during execution.

    Args:
        log_path: Optional path to the log file. If not provided, uses
                  the default path from configuration: data/logs/preprocessing.log

    Returns:
        A configured logger instance.
    """
    if log_path is None:
        config = get_config()
        log_dir = get_path("logs")
        log_path = log_dir / "preprocessing.log"

    # Ensure log directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger("preprocessing")
    logger.setLevel(logging.DEBUG)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # File handler (JSON format)
    file_handler = logging.FileHandler(log_path, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)

    # Console handler (standard format for human readability)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    logger.addHandler(console_handler)

    return logger


def main() -> None:
    """
    Entry point for testing the logging setup.
    Writes a sample log entry to verify JSON formatting.
    """
    logger = setup_preprocessing_logging()

    logger.info("Preprocessing logging initialized successfully.")
    logger.debug("This is a debug message to test the logger.")

    # Example of logging an excluded issue
    excluded_issue = {
        "issue_id": "12345",
        "reason": "missing_timestamps",
        "details": "created_at or closed_at is null"
    }
    logger.warning(
        "Issue excluded due to invalid timestamps",
        extra={"extra_data": excluded_issue}
    )

    logger.info("Logging test completed.")


if __name__ == "__main__":
    main()