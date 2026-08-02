from __future__ import annotations

import json
import logging
import logging.handlers
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from orchestrator.config import load_config

# Global state for the current run ID
_current_run_id: Optional[str] = None
_logger_instance: Optional[logging.Logger] = None


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs.
    Includes run_id, timestamp, level, message, and extra context.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "run_id": getattr(record, "run_id", _current_run_id),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra context passed via extra={} in log calls
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data)

def init_logger(run_id: Optional[str] = None, log_level: str = "INFO") -> logging.Logger:
    """
    Initialize and configure the project logger.

    - Creates the output directory `data/raw/` if it doesn't exist.
    - Sets up a rotating file handler writing JSON logs to `data/raw/orchestrator.log`.
    - Stores the generated or provided `run_id` globally for use in log records.
    - Returns the configured logger instance.

    Args:
        run_id: Optional UUID string. If None, a new UUID is generated.
        log_level: Logging level (e.g., "DEBUG", "INFO").

    Returns:
        The configured logging.Logger instance.
    """
    global _current_run_id, _logger_instance

    if _logger_instance is not None:
        return _logger_instance

    # Generate or use provided run_id
    if run_id is None:
        _current_run_id = str(uuid.uuid4())
    else:
        _current_run_id = run_id

    # Ensure data/raw directory exists
    log_dir = Path("data/raw")
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file_path = log_dir / "orchestrator.log"

    # Create logger
    logger = logging.getLogger("orchestrator")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        logger.handlers.clear()

    # File Handler (Rotating)
    # Max size 10MB, keep 5 backups
    file_handler = logging.handlers.RotatingFileHandler(
        log_file_path,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(getattr(logging, log_level.upper()))
    file_handler.setFormatter(JSONFormatter())

    # Console Handler (Optional, for immediate feedback during dev)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(JSONFormatter())

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    _logger_instance = logger
    logger.info("Logger initialized", extra={"run_id": _current_run_id})

    return logger


def get_logger() -> logging.Logger:
    """
    Get the current logger instance.
    Raises RuntimeError if init_logger() hasn't been called yet.
    """
    if _logger_instance is None:
        # Auto-initialize if not done, using default config
        try:
            config = load_config()
            log_level = config.orchestrator.get("log_level", "INFO")
        except Exception:
            log_level = "INFO"
        init_logger(log_level=log_level)
    
    if _logger_instance is None:
        raise RuntimeError("Logger not initialized. Call init_logger() first.")
    
    return _logger_instance


def log_with_context(message: str, level: str = "INFO", **kwargs: Any) -> None:
    """
    Convenience wrapper to log a message with additional context data.
    
    Args:
        message: The log message.
        level: Log level string (e.g., "INFO", "ERROR").
        **kwargs: Additional key-value pairs to include in the JSON log.
    """
    logger = get_logger()
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    extra_data = {"extra_data": kwargs}
    logger.log(log_level, message, extra=extra_data)
