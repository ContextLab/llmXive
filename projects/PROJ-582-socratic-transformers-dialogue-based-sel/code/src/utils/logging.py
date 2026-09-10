"""
Structured logging utility for degenerate dialogue events.
Handles events as JSON lines following the schema:
{"event_type": str, "timestamp": str, "details": dict}
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure src is in path for imports when running from project root
# This is a safeguard; proper execution assumes correct PYTHONPATH
_src_path = Path(__file__).resolve().parent.parent.parent
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))


class SocraticJsonFormatter(logging.Formatter):
    """
    Custom logging formatter that outputs log records as JSON lines.
    Each log entry follows the schema:
    {
        "event_type": str,      # Log level name (e.g., 'INFO', 'ERROR')
        "timestamp": str,        # ISO 8601 timestamp with timezone
        "details": dict          # Contains message and extra fields
    }
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record as a JSON string.

        Args:
            record: The log record to format.

        Returns:
            A JSON string representing the log event.
        """
        event_data = {
            "event_type": record.levelname,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": {}
        }

        # Add standard message
        event_data["details"]["message"] = record.getMessage()

        # Add extra fields if present
        if hasattr(record, "details") and isinstance(record.details, dict):
            event_data["details"].update(record.details)

        # Add exception info if present
        if record.exc_info:
            event_data["details"]["exception"] = self.formatException(record.exc_info)

        return json.dumps(event_data)


class SocraticLogger:
    """
    Utility class to manage structured logging for the Socratic project.
    Handles file initialization, logger configuration, and event logging.
    """

    def __init__(self, name: str = "socratic_research", log_dir: Optional[str] = None):
        """
        Initialize the logger.

        Args:
            name: Name of the logger.
            log_dir: Directory to store log files. Defaults to 'projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/data/logs'.
        """
        self.name = name
        self.log_dir = log_dir or str(Path(__file__).resolve().parent.parent.parent / "data" / "logs")
        self._logger = logging.getLogger(name)
        self._logger.setLevel(logging.DEBUG)

        # Prevent duplicate handlers if logger is re-initialized
        if not self._logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Configure file and console handlers with JSON formatting."""
        os.makedirs(self.log_dir, exist_ok=True)
        log_file = Path(self.log_dir) / f"{self.name}.jsonl"

        # File handler for JSON lines
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(SocraticJsonFormatter())

        # Console handler for human-readable output (optional, but useful for debugging)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

        self._logger.addHandler(file_handler)
        self._logger.addHandler(console_handler)

    def log_event(self, event_type: str, message: str, details: Optional[Dict[str, Any]] = None, level: int = logging.INFO) -> None:
        """
        Log a structured event.

        Args:
            event_type: Type of event (e.g., 'DIALOGUE_GENERATION', 'CRITIQUE_APPLIED').
            message: Human-readable message.
            details: Additional dictionary data to include in the event.
            level: Logging level (e.g., logging.INFO, logging.ERROR).
        """
        extra = {"details": details} if details else {}
        self._logger.log(level, message, extra=extra)

    def get_logger(self) -> logging.Logger:
        """
        Return the underlying logging.Logger instance.

        Returns:
            The configured logger.
        """
        return self._logger


def get_logger(name: str = "socratic_research", log_dir: Optional[str] = None) -> SocraticLogger:
    """
    Convenience function to retrieve or create a SocraticLogger instance.

    Args:
        name: Name of the logger.
        log_dir: Directory for log files.

    Returns:
        A configured SocraticLogger instance.
    """
    # Simple cache to avoid re-creating loggers with same name in same process
    if not hasattr(get_logger, "_instances"):
        get_logger._instances = {}

    key = (name, log_dir)
    if key not in get_logger._instances:
        get_logger._instances[key] = SocraticLogger(name, log_dir)

    return get_logger._instances[key]


def log_event(event_type: str, message: str, details: Optional[Dict[str, Any]] = None, level: int = logging.INFO, logger_name: str = "socratic_research") -> None:
    """
    Convenience function to log an event directly without managing the logger instance.

    Args:
        event_type: Type of event.
        message: Log message.
        details: Additional data.
        level: Logging level.
        logger_name: Name of the logger to use.
    """
    logger = get_logger(logger_name)
    logger.log_event(event_type, message, details, level)


def init_default_logger(log_dir: Optional[str] = None) -> SocraticLogger:
    """
    Initialize and return the default project logger.

    Args:
        log_dir: Optional override for log directory.

    Returns:
        The default logger instance.
    """
    return get_logger("socratic_research", log_dir)


def main() -> None:
    """
    Entry point for testing the logging utility directly.
    Writes sample events to verify JSON structure.
    """
    logger = init_default_logger()

    # Sample degenerate dialogue event
    logger.log_event(
        event_type="DIALOGUE_START",
        message="Starting dialogue generation for sample ID 123",
        details={"sample_id": 123, "source": "GSM8K", "timestamp": "2026-01-01T00:00:00Z"},
        level=logging.INFO
    )

    # Sample degenerate event (rejection)
    logger.log_event(
        event_type="CRITIQUE_REJECTION",
        message="Candidate answer rejected due to logical contradiction",
        details={"reason": "contradiction", "candidate_index": 2, "error_phrase": "division by zero"},
        level=logging.WARNING
    )

    # Sample error event
    logger.log_event(
        event_type="MODEL_LOAD_ERROR",
        message="Failed to load critic model",
        details={"model_id": "small-critic-v1", "error": "Out of Memory"},
        level=logging.ERROR
    )

    print("Logging test completed. Check data/logs/socratic_research.jsonl for output.")


if __name__ == "__main__":
    main()