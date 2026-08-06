"""
Structured logging utility for the Socratic Transformers project.

This module provides a specialized logger for handling degenerate dialogue events
and standard research logs as JSON lines. It ensures that all critical events,
including errors, timeouts, and model failures, are recorded in a machine-readable
format for downstream statistical analysis (T047, T027).

Implements the Edge Case requirement for degenerate dialogue events.
"""
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from src.utils.config import get_config


class SocraticJsonFormatter(logging.Formatter):
    """
    A custom logging formatter that outputs log records as JSON lines.

    This is essential for parsing logs by downstream analysis scripts (T027, T047)
    and for handling degenerate events (e.g., OOM, timeouts) in a structured way.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
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

        # Include extra fields if present in the record
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data)


class SocraticLogger:
    """
    A wrapper around Python's standard logging to provide structured JSON output
    and specific utilities for the Socratic project.

    This logger handles:
    - Standard info/debug logs as JSON.
    - Degenerate dialogue events (e.g., generation failures, OOMs) with structured context.
    """

    def __init__(self, name: str = "socratic_research", log_level: int = logging.INFO):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)

        # Prevent duplicate handlers if logger is re-initialized
        if not self.logger.handlers:
            # Create console handler
            ch = logging.StreamHandler(sys.stdout)
            ch.setLevel(log_level)
            ch.setFormatter(SocraticJsonFormatter())
            self.logger.addHandler(ch)

            # Ensure file handler is set up if configured
            self._setup_file_handler()

    def _setup_file_handler(self) -> None:
        """
        Sets up a file handler for the logger, writing to the project's log directory.
        The path is derived from the configuration or defaults to a safe location.
        """
        try:
            config = get_config()
            # Ensure the directory exists
            log_dir = Path(config.log_dir)
            log_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = log_dir / "socratic_run.log"
            
            # Check if we already have a file handler to avoid duplicates
            has_file_handler = any(
                isinstance(h, logging.FileHandler) for h in self.logger.handlers
            )
            
            if not has_file_handler:
                fh = logging.FileHandler(log_file)
                fh.setLevel(logging.INFO)
                fh.setFormatter(SocraticJsonFormatter())
                self.logger.addHandler(fh)
        except Exception as e:
            # Fallback to console only if file setup fails
            self.logger.warning(f"Failed to initialize file logger: {e}")

    def log_event(self, event_type: str, message: str, **kwargs: Any) -> None:
        """
        Logs a structured event with a specific type and additional context.

        Args:
            event_type: A categorical label for the event (e.g., 'dialogue_gen', 'timeout', 'oom').
            message: The human-readable message.
            **kwargs: Additional key-value pairs to include in the JSON log entry.
        """
        extra_data = {"event_type": event_type, **kwargs}
        self.logger.info(message, extra={"extra_data": extra_data})

    def log_degenerate_event(self, event_type: str, message: str, **kwargs: Any) -> None:
        """
        Specifically logs degenerate or error events (e.g., model failure, timeout).
        These are critical for the ablation and statistical analysis phases.

        Args:
            event_type: Type of degenerate event (e.g., 'generation_failure', 'timeout', 'validation_error').
            message: Description of the failure.
            **kwargs: Contextual data (e.g., token_count, error_code, attempt_id).
        """
        extra_data = {"event_type": event_type, "severity": "critical", **kwargs}
        self.logger.error(message, extra={"extra_data": extra_data})

    def info(self, msg: str, **kwargs: Any) -> None:
        if kwargs:
            self.log_event("info", msg, **kwargs)
        else:
            self.logger.info(msg)

    def debug(self, msg: str, **kwargs: Any) -> None:
        if kwargs:
            self.log_event("debug", msg, **kwargs)
        else:
            self.logger.debug(msg)

    def warning(self, msg: str, **kwargs: Any) -> None:
        if kwargs:
            self.log_event("warning", msg, **kwargs)
        else:
            self.logger.warning(msg)

    def error(self, msg: str, **kwargs: Any) -> None:
        if kwargs:
            self.log_event("error", msg, **kwargs)
        else:
            self.logger.error(msg)

    def critical(self, msg: str, **kwargs: Any) -> None:
        if kwargs:
            self.log_event("critical", msg, **kwargs)
        else:
            self.logger.critical(msg)


# Global logger instance for convenience
_global_logger: Optional[SocraticLogger] = None


def get_logger(name: str = "socratic_research") -> SocraticLogger:
    """
    Retrieves or creates a global logger instance.

    Args:
        name: The name of the logger. Defaults to 'socratic_research'.

    Returns:
        A configured SocraticLogger instance.
    """
    global _global_logger
    if _global_logger is None or _global_logger.name != name:
        _global_logger = SocraticLogger(name)
    return _global_logger


if __name__ == "__main__":
    # Simple demonstration of the logger output format
    logger = get_logger()
    logger.info("Logger initialized successfully.")
    logger.log_event("system_check", "Environment loaded", cpu_count=4)
    logger.log_degenerate_event(
        "timeout", 
        "Training loop exceeded time limit", 
        timeout_seconds=300, 
          model_id="test-model"
    )
    logger.warning("This is a standard warning message.")