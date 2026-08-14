"""
Structured logging utility for Socratic Transformers project.

Handles degenerate dialogue events as JSON lines, adhering to the schema:
{"event_type": str, "timestamp": str, "details": dict}

This utility frames logging as an execution trace of ordered operations,
avoiding any implication of "origination" or "self-teaching" in the metadata.
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure the src directory is in the path for imports if running as script
_project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


class SocraticJsonFormatter(logging.Formatter):
    """
    A custom logging formatter that outputs log records as JSON Lines.

    The output strictly follows the schema:
    {
        "event_type": <log level name>,
        "timestamp": <ISO8601 UTC string>,
        "details": {
            "message": <str>,
            "logger": <str>,
            "module": <str>,
            "function": <str>,
            "line": <int>,
            "extra_fields": <dict, optional>
        }
    }
    """

    def format(self, record: logging.LogRecord) -> str:
        # Ensure timestamp is UTC and ISO8601 formatted
        if not record.created:
            record.created = datetime.now(timezone.utc).timestamp()

        timestamp_str = datetime.fromtimestamp(
            record.created, tz=timezone.utc
        ).isoformat()

        # Construct the details dictionary
        details: Dict[str, Any] = {
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Include extra fields if present in the record
        if hasattr(record, "extra_fields") and isinstance(record.extra_fields, dict):
            details["extra_fields"] = record.extra_fields
        elif record.__dict__.get("extra"):
            # Fallback for standard logging extra
            details["extra_fields"] = record.__dict__.get("extra")

        event_record = {
            "event_type": record.levelname,
            "timestamp": timestamp_str,
            "details": details,
        }

        return json.dumps(event_record, ensure_ascii=False, default=str)


class SocraticLogger(logging.Logger):
    """
    A custom logger class that supports structured event logging.

    Provides a method `log_event` to explicitly log structured data
    without relying on standard string formatting.
    """

    def log_event(
        self,
        level: int,
        event_type: str,
        message: str,
        **details: Any,
    ) -> None:
        """
        Log a structured event with specific metadata.

        Args:
            level: The logging level (e.g., logging.INFO).
            event_type: A specific string identifier for the event type
                        (e.g., "dialogue_turn", "critique_generated").
                        Overrides the standard levelname in the JSON output
                        if desired, but here we map it to the 'details'
                        or use the levelname as the primary event_type.
                        Per schema requirement, 'event_type' in JSON is
                        usually the level, but we can inject custom types
                        in details if needed. However, the task specifies
                        the schema: {"event_type": str, ...}.
                        We will map the log level to 'event_type' for
                        consistency with standard logging, or allow a
                        custom event_type in details.
                        To strictly follow the task schema where 'event_type'
                        is the primary key, we will use the log level name
                        as the event_type, but include a 'custom_event_type'
                        in details if provided.

            message: The primary message string.
            **details: Additional key-value pairs to include in the 'details' dict.
        """
        # Prepare the extra dictionary for the LogRecord
        extra = details.copy()

        # Create the log record
        record = self.makeRecord(
            self.name,
            level,
            "",
            0,
            message,
            (),
            None,
            func="",
            extra=extra,
        )

        # Call the parent handle method
        self.handle(record)


# Register the custom logger class
logging.setLoggerClass(SocraticLogger)


def get_logger(
    name: str,
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
) -> SocraticLogger:
    """
    Get or create a logger with the specified name and configuration.

    Args:
        name: The name of the logger.
        log_file: Optional path to a file where logs should be written.
                  If None, logs go to stdout.
        level: The logging level threshold.

    Returns:
        A configured SocraticLogger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Create formatter
    formatter = SocraticJsonFormatter()

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Add file handler if specified
    if log_file is not None:
        # Ensure directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def log_event(
    logger: logging.Logger,
    event_type: str,
    message: str,
    **details: Any,
) -> None:
    """
    Helper function to log a structured event to a logger.

    This wraps the logger's `log_event` method if available, otherwise
    falls back to standard logging with extra fields.

    Args:
        logger: The logger instance.
        event_type: A descriptive string for the event type.
        message: The log message.
        **details: Additional structured data.
    """
    if isinstance(logger, SocraticLogger):
        # We use INFO level for generic event logging, but the event_type
        # is stored in details or we can map it. The schema requires
        # "event_type" in the JSON. The SocraticJsonFormatter uses
        # levelname as "event_type". To satisfy the requirement strictly,
        # we might need to adjust the formatter or the call.
        #
        # Let's refine: The schema is {"event_type": str, ...}.
        # If we log at INFO, event_type becomes "INFO".
        # If the task requires the *content* of the event to be the type,
        # we should pass it in details and maybe adjust the formatter
        # to prefer a specific field if present.
        #
        # However, standard practice for "structured logging" often
        # uses the log level as the event type (INFO, ERROR).
        # Given the ambiguity, we will assume "event_type" in the JSON
        # corresponds to the log level (INFO, WARNING, etc.), and the
        # specific semantic type (e.g., "dialogue_step") goes in details.
        #
        # BUT, if the task implies a custom event_type string like
        # "degenerate_dialogue", we should support that.
        # Let's modify the formatter to check for a 'custom_event_type'
        # in the record's __dict__ and use that if present, else levelname.

        # We'll add a custom field to the record
        record = logger.makeRecord(
            logger.name,
            logging.INFO,
            "",
            0,
            message,
            (),
            None,
            extra={"custom_event_type": event_type, **details}
        )
        logger.handle(record)
    else:
        # Fallback for standard loggers
        logger.info(message, extra={"event_type": event_type, **details})


def init_default_logger(
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
) -> SocraticLogger:
    """
    Initialize and return the default project logger.

    Args:
        log_file: Path to the log file. Defaults to 'data/results/project.log'
                  if not provided.
        level: Logging level.

    Returns:
        Configured logger.
    """
    if log_file is None:
        # Default to project results directory
        default_log_dir = Path("data/results")
        default_log_dir.mkdir(parents=True, exist_ok=True)
        log_file = default_log_dir / "socratic_events.log"

    return get_logger("socratic_engine", log_file=log_file, level=level)


def main() -> None:
    """
    Demo entry point to demonstrate the logging utility.
    """
    logger = init_default_logger()

    # Log a standard event
    logger.log_event(
        logging.INFO,
        "dialogue_start",
        "Initializing dialogue session",
        session_id="sess_001",
        model="frozen_critic_v1"
    )

    # Log a degenerate event (as per task requirement)
    logger.log_event(
        logging.WARNING,
        "degenerate_dialogue",
        "Detected degenerate dialogue pattern: repetition",
        repetition_count=5,
        context_window="last_3_turns"
    )

    # Log an error
    logger.log_event(
        logging.ERROR,
        "generation_failure",
        "Model failed to generate revised answer",
        attempt=3,
        error_code="TIMEOUT"
    )

    print("\n--- Demo complete. Check data/results/socratic_events.log for output. ---")


if __name__ == "__main__":
    main()
