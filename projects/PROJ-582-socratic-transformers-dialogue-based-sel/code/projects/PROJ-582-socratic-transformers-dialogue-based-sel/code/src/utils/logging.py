"""
Structured logging utility for degenerate dialogue events.

This module implements a JSON-based logging formatter and helper utilities
to handle dialogue events in the Socratic Transformers pipeline. Events are
logged as JSON lines (one JSON object per line) following the schema:
{"event_type": str, "timestamp": str, "details": dict}
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union


class SocraticJsonFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging of dialogue events.

    Formats log records as JSON lines with the schema:
    {
        "event_type": str,       # Derived from log level or custom field
        "timestamp": str,         # ISO 8601 timestamp
        "details": dict           # Contains message and extra context
    }
    """

    def __init__(self, event_type_prefix: str = "socratic"):
        """
        Initialize the formatter.

        Args:
            event_type_prefix: Prefix for event_type field (e.g., "socratic_debug")
        """
        super().__init__()
        self.event_type_prefix = event_type_prefix

    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record as a JSON line.

        Args:
            record: The log record to format

        Returns:
            JSON string representation of the log record
        """
        # Build the event_type from log level
        level_name = record.levelname.lower()
        event_type = f"{self.event_type_prefix}_{level_name}"

        # Build the details dictionary
        details: Dict[str, Any] = {
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add any extra fields passed via extra={}
        if hasattr(record, "details"):
            if isinstance(record.details, dict):
                details.update(record.details)
            else:
                details["extra_data"] = record.details

        # Create the event object
        event = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "details": details,
        }

        return json.dumps(event, ensure_ascii=False, default=str)


class SocraticLogger:
    """
    Utility class for managing structured dialogue event logging.

    Provides a consistent interface for creating and configuring loggers
    that output JSON lines to files or stdout.
    """

    def __init__(self, name: str = "socratic_dialogue"):
        """
        Initialize the logger manager.

        Args:
            name: Name for the logger instance
        """
        self.name = name
        self._logger: Optional[logging.Logger] = None

    def get_logger(
        self,
        log_path: Optional[Union[str, Path]] = None,
        level: int = logging.INFO,
        include_stdout: bool = True,
        event_type_prefix: str = "socratic",
    ) -> logging.Logger:
        """
        Get or create a configured logger instance.

        Args:
            log_path: Path to log file (optional). If None, only stdout is used.
            level: Logging level (e.g., logging.DEBUG, logging.INFO)
            include_stdout: Whether to also log to stdout
            event_type_prefix: Prefix for event_type field in JSON

        Returns:
            Configured logger instance
        """
        if self._logger is not None:
            return self._logger

        # Create logger
        logger = logging.getLogger(self.name)
        logger.setLevel(level)
        logger.propagate = False  # Prevent duplicate logs

        # Clear any existing handlers
        logger.handlers.clear()

        # Create formatter
        formatter = SocraticJsonFormatter(event_type_prefix=event_type_prefix)

        # Add file handler if path provided
        if log_path:
            log_file = Path(log_path)
            log_file.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
            file_handler.setFormatter(formatter)
            file_handler.setLevel(level)
            logger.addHandler(file_handler)

        # Add stdout handler if requested
        if include_stdout:
            stdout_handler = logging.StreamHandler(sys.stdout)
            stdout_handler.setFormatter(formatter)
            stdout_handler.setLevel(level)
            logger.addHandler(stdout_handler)

        self._logger = logger
        return logger

    def log_event(
        self,
        event_type: str,
        details: Dict[str, Any],
        level: int = logging.INFO,
        message: Optional[str] = None,
    ) -> None:
        """
        Log a structured dialogue event.

        Args:
            event_type: Type of event (e.g., "critique_generated", "dialogue_step")
            details: Dictionary of event-specific details
            level: Logging level
            message: Optional message to include in details
        """
        if self._logger is None:
            # Initialize with defaults if not set up
            self.get_logger()

        # Prepare the log record
        log_message = message or details.get("message", event_type)

        # Log with extra details
        self._logger.log(
            level,
            log_message,
            extra={"details": details},
        )


# Global logger instance
_global_logger: Optional[SocraticLogger] = None


def get_logger(name: str = "socratic_dialogue") -> SocraticLogger:
    """
    Get or create the global SocraticLogger instance.

    Args:
        name: Name for the logger instance

    Returns:
        SocraticLogger instance
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = SocraticLogger(name)
    return _global_logger


def log_event(
    event_type: str,
    details: Dict[str, Any],
    level: int = logging.INFO,
    message: Optional[str] = None,
    logger_name: str = "socratic_dialogue",
) -> None:
    """
    Convenience function to log a structured dialogue event.

    Args:
        event_type: Type of event (e.g., "critique_generated", "dialogue_step")
        details: Dictionary of event-specific details
        level: Logging level
        message: Optional message to include
        logger_name: Name of the logger to use
    """
    logger_instance = get_logger(logger_name)
    logger_instance.log_event(event_type, details, level, message)


def init_default_logger(
    log_dir: Union[str, Path] = "data/logs",
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Initialize a default logger with file output.

    Args:
        log_dir: Directory to store log files
        level: Logging level

    Returns:
        Configured logger instance
    """
    log_path = Path(log_dir) / "dialogue_events.jsonl"
    logger_instance = get_logger()
    return logger_instance.get_logger(
        log_path=log_path,
        level=level,
        include_stdout=True,
    )


# Module-level convenience function for direct logging
def main() -> None:
    """
    Demo function showing how to use the structured logger.
    """
    # Initialize logger
    logger = init_default_logger()

    # Log some example events
    logger.log_event(
        event_type="dialogue_started",
        details={
            "question_id": "gsm8k_12345",
            "question": "What is 2+2?",
            "initial_answer": "4",
        },
        message="Starting dialogue for question",
    )

    logger.log_event(
        event_type="critique_generated",
        details={
            "critique_tokens": 45,
            "keywords_found": ["contradiction", "error"],
            "quality_score": 0.85,
        },
        message="Critique generated successfully",
    )

    logger.log_event(
        event_type="dialogue_completed",
        details={
            "revised_answer": "The answer is 4",
            "total_turns": 3,
        },
        message="Dialogue completed",
    )


if __name__ == "__main__":
    main()