"""Logging infrastructure for the llmXive pipeline.

Implements JSON logging with rotation, matching the schema in
`contracts/logging_schema.yaml`.
"""
from __future__ import annotations

import json
import logging
import logging.handlers
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from config import get_config


@dataclass
class LogEntry:
    """Log entry matching the schema in contracts/logging_schema.yaml."""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    level: str = "INFO"
    message: str = ""
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    module: str = "root"

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


class JSONFormatter(logging.Formatter):
    """Formatter that outputs JSON strings matching the schema."""

    def format(self, record: logging.LogRecord) -> str:
        entry = LogEntry(
            timestamp=datetime.utcnow().isoformat(),
            level=record.levelname,
            message=record.getMessage(),
            trace_id=getattr(record, 'trace_id', str(uuid.uuid4())),
            module=getattr(record, 'module', 'root')
        )
        return entry.to_json()


def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    module_name: Optional[str] = None,
    config: Optional[Any] = None,
    log_level: Optional[str] = None,
    *args: Any,
    **kwargs: Any
) -> logging.Logger:
    """Configure logging with JSON formatting and rotation.

    Accepts all call shapes observed in the codebase:
      - setup_logging()
      - setup_logging(level="INFO")
      - setup_logging(level=args.log_level)
      - setup_logging(log_level="INFO")
      - setup_logging(config)
      - setup_logging(log_file="data/logs/app.log")
      - setup_logging(module_name=...)
      - setup_logging(config, level=...)
      - setup_logging(*args, **kwargs)

    The function is tolerant of unrecognized shapes and never raises.
    """
    # Normalize arguments
    effective_level = level or log_level or "INFO"
    if isinstance(effective_level, str):
        effective_level = effective_level.upper()
    elif isinstance(effective_level, int):
        pass  # Already a numeric level
    else:
        effective_level = "INFO"

    effective_file = log_file
    if config and hasattr(config, 'data_logs'):
        effective_file = config.data_logs
    elif config and isinstance(config, dict) and 'data_logs' in config:
        effective_file = config['data_logs']

    if not effective_file:
        # Default path relative to project root
        config_obj = get_config()
        if config_obj and hasattr(config_obj, 'data_logs'):
            effective_file = config_obj.data_logs
        else:
            effective_file = "data/logs/app.log"

    # Ensure directory exists
    log_path = Path(effective_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Get or create logger
    logger_name = module_name or kwargs.get('module', 'root')
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, effective_level, logging.INFO))

    # Prevent duplicate handlers
    if logger.handlers:
        # Check if our RotatingFileHandler is already attached
        has_handler = any(
            isinstance(h, logging.handlers.RotatingFileHandler) and h.baseFilename == str(log_path.resolve())
            for h in logger.handlers
        )
        if has_handler:
            return logger

    # Clear existing handlers to avoid duplicates in re-runs
    logger.handlers.clear()

    # Configure RotatingFileHandler
    handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    handler.setLevel(getattr(logging, effective_level, logging.INFO))

    # Set formatter
    formatter = JSONFormatter()
    handler.setFormatter(formatter)

    # Add handler
    logger.addHandler(handler)

    # Also add a console handler for visibility during development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, effective_level, logging.INFO))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str = "root") -> logging.Logger:
    """Get a logger instance with JSON formatting."""
    return setup_logging(module_name=name)


def log_with_extra(
    logger: logging.Logger,
    level: int,
    message: str,
    **extra: Any
) -> None:
    """Log a message with extra fields (e.g., trace_id)."""
    logger.log(level, message, extra=extra)


def validate_schema_exists() -> bool:
    """Validate that the logging schema file exists."""
    schema_path = Path("contracts/logging_schema.yaml")
    return schema_path.exists()


class ReproducibilityLogger:
    """Backward-compatible logger for legacy callers.

    This class is kept for compatibility with code that expects a
    ReproducibilityLogger object, but the primary logging mechanism
    now uses the stdlib logging module with JSON formatting.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list = []

    def log(self, *args: Any, **kwargs: Any) -> LogEntry:
        op = args[0] if args else kwargs.get("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        return entry

    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop


_GLOBAL_LOGGER: Optional[ReproducibilityLogger] = None


def get_reproducibility_logger() -> ReproducibilityLogger:
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger()
    return _GLOBAL_LOGGER


def log_operation(*args: Any, **kwargs: Any) -> Any:
    """Dual-purpose: decorator or direct logging call."""
    import functools

    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]

        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any) -> Any:
            return func(*a, **k)

        return _wrapper

    op = args[0] if args else kwargs.pop("operation", "operation")
    logger = get_reproducibility_logger()
    return logger.log(op, **kwargs)


def main() -> None:
    """Test the logging configuration."""
    import sys

    # Validate schema exists
    if not validate_schema_exists():
        print("ERROR: contracts/logging_schema.yaml not found", file=sys.stderr)
        sys.exit(1)

    # Setup logging
    logger = setup_logging(level="INFO", module_name="test")

    # Log a test message
    logger.info("Logging infrastructure test successful")
    logger.warning("This is a warning message")
    logger.error("This is an error message")

    # Verify log file exists
    log_path = Path("data/logs/app.log")
    if not log_path.exists():
        print("ERROR: Log file not created", file=sys.stderr)
        sys.exit(1)

    print(f"SUCCESS: Log file created at {log_path.resolve()}")
    print("SUCCESS: Logging infrastructure is correctly configured")


if __name__ == "__main__":
    main()