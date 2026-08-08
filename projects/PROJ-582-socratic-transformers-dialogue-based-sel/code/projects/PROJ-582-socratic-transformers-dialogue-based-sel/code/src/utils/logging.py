"""
Structured logging utility for degenerate dialogue events.

This module implements a JSON-line based logger specifically designed for the
Socratic Transformers project. It handles events related to dialogue generation,
critique application, and selection processes, ensuring all logs adhere to the
schema: {"event_type": str, "timestamp": str, "details": dict}.

The logger writes to files in the `data/processed/` or `data/results/` directories
as configured, supporting high-throughput event logging without the overhead of
traditional formatted string logs.
"""
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

class SocraticJsonFormatter(logging.Formatter):
    """
    Custom formatter that outputs log records as JSON lines.

    The output format adheres to the project's event schema:
    {
        "event_type": str,
        "timestamp": str (ISO 8601),
        "details": {
            "level": str,
            "logger_name": str,
            "message": str,
            "extra_fields": dict (any additional keys from log record)
        }
    }
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record as a JSON string.

        Args:
            record: The log record to format.

        Returns:
            A JSON string representing the event.
        """
        # Extract standard fields
        event_type = getattr(record, 'event_type', 'generic_log')
        timestamp = datetime.utcnow().isoformat() + 'Z'

        # Build the details dictionary
        details = {
            "level": record.levelname,
            "logger_name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add any extra attributes passed to the log call
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in ('name', 'msg', 'args', 'created', 'filename',
                           'funcName', 'levelname', 'levelno', 'lineno',
                           'module', 'msecs', 'message', 'pathname',
                           'process', 'processName', 'relativeCreated',
                           'stack_info', 'exc_info', 'exc_text', 'thread',
                           'threadName', 'taskName', 'event_type'):
                try:
                    # Attempt to serialize; skip if not serializable
                    json.dumps(value)
                    extra_fields[key] = value
                except (TypeError, ValueError):
                    extra_fields[key] = str(value)

        if extra_fields:
            details["extra_fields"] = extra_fields

        event = {
            "event_type": event_type,
            "timestamp": timestamp,
            "details": details
        }

        return json.dumps(event)


class SocraticLogger(logging.Logger):
    """
    Custom Logger class that supports structured event logging.

    Adds convenience methods for logging specific event types common in
    the Socratic pipeline (e.g., critique_generated, selection_applied).
    """

    def event(self, event_type: str, message: str, **kwargs: Any) -> None:
        """
        Log an event with a specific type and details.

        Args:
            event_type: The type of event (e.g., 'critique_generated').
            message: The human-readable message.
            **kwargs: Additional details to include in the 'details' field.
        """
        extra = kwargs.copy()
        extra['event_type'] = event_type
        self.info(message, extra=extra)

    def log_dialogue_event(self, event_type: str, question_id: str,
                           initial_answer: str, critique: Optional[str] = None,
                           revised_answer: Optional[str] = None, **kwargs: Any) -> None:
        """
        Log a specific dialogue generation event.

        Args:
            event_type: The type of event (e.g., 'dialogue_generated', 'dialogue_discarded').
            question_id: Unique identifier for the question.
            initial_answer: The model's initial answer.
            critique: The generated critique (optional).
            revised_answer: The revised answer (optional).
            **kwargs: Additional details.
        """
        details = {
            "question_id": question_id,
            "initial_answer": initial_answer,
            "critique": critique,
            "revised_answer": revised_answer,
            **kwargs
        }
        extra = details
        extra['event_type'] = event_type
        self.info("Dialogue event processed", extra=extra)


# Register the custom logger class
logging.setLoggerClass(SocraticLogger)


def get_logger(name: str, log_file: Optional[Path] = None,
               level: int = logging.INFO) -> SocraticLogger:
    """
    Get or create a SocraticLogger instance.

    If a log file path is provided, a FileHandler with SocraticJsonFormatter
    is attached to the logger.

    Args:
        name: The name of the logger.
        log_file: Optional path to a log file. If provided, logs are written here.
        level: The logging level.

    Returns:
        A configured SocraticLogger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times if logger is requested repeatedly
    if not logger.handlers:
        # Console handler (optional, for debugging, usually JSON is for files)
        # For production, we might only want file output, but let's allow console
        # if no file is specified or explicitly desired. Here we default to file if path given.
        if log_file:
            # Ensure directory exists
            log_file.parent.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(log_file)
            fh.setLevel(level)
            fh.setFormatter(SocraticJsonFormatter())
            logger.addHandler(fh)

    return logger


# Convenience function for quick logging without explicit logger management
def log_event(event_type: str, message: str, log_file: Path,
              **details: Any) -> None:
    """
    Quick function to log a single event to a file.

    Args:
        event_type: The type of event.
        message: The log message.
        log_file: Path to the output JSONL file.
        **details: Additional key-value pairs for the event details.
    """
    logger = get_logger("socratic_event", log_file=log_file)
    logger.event(event_type, message, **details)
