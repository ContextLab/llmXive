"""
Structured logging utility for Socratic Transformers dialogue events.

Handles degenerate dialogue events as JSON lines with the schema:
{"event_type": str, "timestamp": str, "details": dict}
"""
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


class SocraticJsonFormatter(logging.Formatter):
    """Custom formatter that outputs log records as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as a JSON line."""
        event_data: Dict[str, Any] = {
            "event_type": record.levelname,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": {
                "message": record.getMessage(),
                "logger": record.name,
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            },
        }

        # Add extra fields if present
        if hasattr(record, "details") and isinstance(record.details, dict):
            event_data["details"].update(record.details)

        return json.dumps(event_data)


class SocraticLogger(logging.Logger):
    """Extended logger with convenience methods for structured logging."""

    def log_event(self, event_type: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Log a structured event.

        Args:
            event_type: The type of event (e.g., "DIALOGUE_STEP", "CRITIQUE_GENERATED")
            message: The main message text
            details: Additional structured data to include
        """
        extra = {"details": details} if details else {}
        self.info(message, extra=extra)


# Register custom logger class
logging.setLoggerClass(SocraticLogger)


def get_logger(name: str, log_path: Optional[str] = None, level: int = logging.INFO) -> SocraticLogger:
    """
    Get or create a logger with JSON formatting.

    Args:
        name: Logger name (usually __name__)
        log_path: Optional path to write log file. If None, logs to stderr.
        level: Logging level

    Returns:
        Configured SocraticLogger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Create formatter
    formatter = SocraticJsonFormatter()

    # Add file handler if path provided
    if log_path:
        log_file = Path(log_path)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Always add console handler for visibility
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger  # type: ignore[return-value]


# Global logger instance
_global_logger: Optional[SocraticLogger] = None


def log_event(event_type: str, message: str, details: Optional[Dict[str, Any]] = None, log_path: str = "test.log") -> None:
    """
    Convenience function to log an event to a file.

    This function creates a logger instance, logs the event, and ensures
    the output is written to the specified log file as JSON lines.

    Args:
        event_type: Type of event (e.g., "TEST", "INFO", "ERROR")
        message: The message to log
        details: Optional dictionary of additional details
        log_path: Path to the log file (default: "test.log")
    """
    global _global_logger

    if _global_logger is None:
        _global_logger = get_logger("socratic_logger", log_path=log_path)

    # Map event_type to log level
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    level = level_map.get(event_type.upper(), logging.INFO)

    # Log with the appropriate level
    _global_logger.log(level, message, extra={"details": details} if details else {})


def init_default_logger(log_path: str = "socratic.log") -> SocraticLogger:
    """
    Initialize and return the default project logger.

    Args:
        log_path: Path to the default log file

    Returns:
        The initialized logger instance
    """
    global _global_logger
    _global_logger = get_logger("socratic", log_path=log_path)
    return _global_logger


def main() -> None:
    """Test the logging functionality."""
    # Initialize logger with test output
    logger = init_default_logger("test.log")

    # Log some test events
    log_event("INFO", "Test event 1", {"test_key": "test_value"})
    log_event("DEBUG", "Debug message", {"debug_info": 123})
    log_event("WARNING", "Warning message")

    # Verify file exists and contains valid JSON
    assert os.path.exists("test.log"), "Log file was not created"

    with open("test.log", "r") as f:
        lines = f.readlines()
        assert len(lines) > 0, "Log file is empty"

        for line in lines:
            try:
                parsed = json.loads(line.strip())
                assert "event_type" in parsed, "Missing event_type"
                assert "timestamp" in parsed, "Missing timestamp"
                assert "details" in parsed, "Missing details"
                assert isinstance(parsed["details"], dict), "Details must be a dict"
            except json.JSONDecodeError as e:
                raise AssertionError(f"Invalid JSON in log file: {line}") from e

    print("Logging test passed successfully!")


if __name__ == "__main__":
    main()