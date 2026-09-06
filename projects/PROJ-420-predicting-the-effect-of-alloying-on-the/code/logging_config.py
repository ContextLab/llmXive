"""
Logging infrastructure for the alloy prediction pipeline.
Implements JSON logging with rotation as per T006 requirements.
"""
from __future__ import annotations

import functools
import json
import logging
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Optional

import yaml

from config import get_config

# Ensure log directory exists
LOG_DIR = Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

# Load schema for validation
SCHEMA_PATH = Path("contracts/logging_schema.yaml")


@dataclass
class LogEntry:
    """Log entry matching the schema defined in contracts/logging_schema.yaml."""
    timestamp: str
    level: str
    message: str
    trace_id: str
    module: str

    def to_json(self) -> str:
        """Serialize to JSON string matching the required schema."""
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict) -> "LogEntry":
        """Create LogEntry from dictionary."""
        required_fields = ["timestamp", "level", "message", "trace_id", "module"]
        for field_name in required_fields:
            if field_name not in data:
                raise ValueError(f"Missing required field: {field_name}")
        return cls(**{k: v for k, v in data.items() if k in required_fields})


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs JSON logs matching the schema."""

    def __init__(self, module_name: str = "root"):
        super().__init__()
        self.module_name = module_name

    def format(self, record: logging.LogRecord) -> str:
        trace_id = getattr(record, "trace_id", str(uuid.uuid4()))
        level = record.levelname

        # Map Python logging levels to standard strings
        level_map = {
            logging.DEBUG: "DEBUG",
            logging.INFO: "INFO",
            logging.WARNING: "WARNING",
            logging.ERROR: "ERROR",
            logging.CRITICAL: "CRITICAL",
        }
        level = level_map.get(record.levelno, level)

        entry = LogEntry(
            timestamp=datetime.utcnow().isoformat(),
            level=level,
            message=record.getMessage(),
            trace_id=trace_id,
            module=self.module_name,
        )
        return entry.to_json()


def setup_logging(
    level: Optional[str] = None,
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    config: Optional[dict] = None,
    module_name: str = "root",
) -> logging.Logger:
    """
    Setup logging infrastructure with JSON formatting and rotation.

    Accepts multiple call signatures for compatibility with various callers:
    - setup_logging()
    - setup_logging(level="INFO")
    - setup_logging(log_level="INFO")
    - setup_logging(config)
    - setup_logging(log_file="data/logs/app.log")
    - setup_logging(level=args.log_level)

    Args:
        level: Log level string (e.g., "INFO")
        log_level: Alternative log level parameter
        log_file: Custom log file path
        config: Configuration dictionary
        module_name: Name of the module for logging

    Returns:
        Configured logger instance
    """
    # Normalize parameters from different call signatures
    effective_level = level or log_level or "INFO"
    effective_log_file = log_file or str(LOG_FILE)

    # Handle config dict if passed as first positional arg
    if config and isinstance(config, dict):
        effective_level = config.get("level", effective_level)
        effective_log_file = config.get("log_file", effective_log_file)
        module_name = config.get("module_name", module_name)

    # Create logger
    logger = logging.getLogger(module_name)
    logger.setLevel(getattr(logging, effective_level.upper(), logging.INFO))

    # Clear existing handlers
    logger.handlers.clear()

    # Ensure log directory exists
    log_path = Path(effective_log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Setup rotating file handler with JSON formatting
    # maxBytes=10MB, backupCount=5 as per requirements
    file_handler = RotatingFileHandler(
        effective_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
    )
    file_handler.setFormatter(JSONFormatter(module_name))
    file_handler.setLevel(getattr(logging, effective_level.upper(), logging.INFO))

    # Setup console handler for visibility
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter(module_name))
    console_handler.setLevel(getattr(logging, effective_level.upper(), logging.INFO))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str = "root") -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)


def log_operation(
    operation: str,
    message: Optional[str] = None,
    level: str = "INFO",
    **kwargs: Any,
) -> LogEntry:
    """
    Log an operation with automatic JSON formatting.

    Can be used as a decorator or direct function call.

    Args:
        operation: Name of the operation being logged
        message: Optional custom message
        level: Log level
        **kwargs: Additional context to include in the log

    Returns:
        LogEntry instance
    """
    # If called as decorator
    if len(kwargs) == 0 and callable(operation):
        @functools.wraps(operation)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return operation(*args, **kwargs)
        return wrapper

    # Direct call
    logger = setup_logging(module_name=kwargs.get("module", "root"))
    trace_id = kwargs.pop("trace_id", str(uuid.uuid4()))

    # Prepare extra context
    extra = {"trace_id": trace_id}

    # Log the message
    log_message = message or operation
    log_method = getattr(logger, level.lower(), logger.info)
    log_method(log_message, extra=extra)

    return LogEntry(
        timestamp=datetime.utcnow().isoformat(),
        level=level.upper(),
        message=log_message,
        trace_id=trace_id,
        module=kwargs.get("module", "root"),
    )


def log_with_extra(
    message: str,
    level: str = "INFO",
    extra: Optional[dict] = None,
    module_name: str = "root",
) -> None:
    """
    Log a message with additional context.

    Args:
        message: Log message
        level: Log level
        extra: Additional context dictionary
        module_name: Module name for the logger
    """
    logger = setup_logging(module_name=module_name)
    log_method = getattr(logger, level.lower(), logger.info)
    log_method(message, extra=extra or {})


# Initialize global logger on module load
_GLOBAL_LOGGER: Optional[logging.Logger] = None


def _get_global_logger() -> logging.Logger:
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = setup_logging()
    return _GLOBAL_LOGGER
