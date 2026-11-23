"""
Structured logging utility for Socratic Transformers project.
Handles degenerate dialogue events as JSON lines.
"""
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from src.utils.config import get_config


class SocraticJsonFormatter(logging.Formatter):
    """
    Custom logging formatter that outputs JSON lines.
    Ensures events follow the schema:
    {"event_type": str, "timestamp": str, "details": dict}
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON line."""
        # Get current timestamp in ISO format with timezone
        timestamp = datetime.now(timezone.utc).isoformat()

        # Extract event type from log level or custom attribute
        event_type = getattr(record, 'event_type', record.levelname.lower())

        # Build details dictionary with standard fields
        details: Dict[str, Any] = {
            "message": record.getMessage(),
            "level": record.levelname,
            "logger": record.name,
        }

        # Add extra fields if present
        if hasattr(record, 'details') and isinstance(record.details, dict):
            details.update(record.details)

        # Add exception info if present
        if record.exc_info:
            details["exception"] = self.formatException(record.exc_info)

        # Construct the final event dictionary
        event = {
            "event_type": event_type,
            "timestamp": timestamp,
            "details": details
        }

        return json.dumps(event)


class SocraticLogger(logging.Logger):
    """
    Custom logger class that supports structured event logging.
    """

    def event(self, event_type: str, message: str, **kwargs) -> None:
        """
        Log a structured event.

        Args:
            event_type: Type of event (e.g., 'dialogue_start', 'critique_generated')
            message: Human-readable message
            **kwargs: Additional details to include in the event
        """
        extra = {
            'event_type': event_type,
            'details': kwargs
        }
        self.info(message, extra=extra)


# Register custom logger class
logging.setLoggerClass(SocraticLogger)


def get_logger(name: str, log_file: Optional[str] = None) -> SocraticLogger:
    """
    Get a configured SocraticLogger instance.

    Args:
        name: Logger name (typically __name__)
        log_file: Optional path to log file. If None, logs to console.

    Returns:
        Configured SocraticLogger instance
    """
    logger = logging.getLogger(name)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Create formatter
    formatter = SocraticJsonFormatter()

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Add file handler if log_file specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def log_event(logger: logging.Logger, event_type: str, message: str, **details) -> None:
    """
    Convenience function to log a structured event.

    Args:
        logger: Logger instance
        event_type: Type of event
        message: Human-readable message
        **details: Additional event details
    """
    if hasattr(logger, 'event'):
        logger.event(event_type, message, **details)
    else:
        extra = {
            'event_type': event_type,
            'details': details
        }
        logger.info(message, extra=extra)


def init_default_logger(project_root: Optional[Path] = None) -> SocraticLogger:
    """
    Initialize the default logger for the project.

    Args:
        project_root: Optional project root path. If None, uses config.

    Returns:
        Configured default logger
    """
    config = get_config()
    log_dir = project_root / "logs" if project_root else Path(config.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "socratic_events.jsonl"
    return get_logger(__name__, str(log_file))


def main() -> None:
    """
    Demonstrate the logging utility with sample events.
    """
    logger = init_default_logger()

    # Log a dialogue start event
    log_event(
        logger,
        "dialogue_start",
        "Starting Socratic dialogue generation",
        sample_id="12345",
        question="What is the capital of France?"
    )

    # Log a critique generation event
    log_event(
        logger,
        "critique_generated",
        "Generated critique for initial answer",
        critique_length=45,
        keywords_found=["contradiction", "error"]
    )

    # Log a degenerate event (empty critique)
    log_event(
        logger,
        "degenerate_event",
        "Detected degenerate dialogue event: empty critique",
        sample_id="12345",
        reason="critique_too_short",
        token_count=0
    )

    # Log a revised answer event
    log_event(
        logger,
        "revised_answer_generated",
        "Generated revised answer after critique",
        sample_id="12345",
        confidence_score=0.85
    )

    print("Logging demonstration completed. Check logs/socratic_events.jsonl")


if __name__ == "__main__":
    main()