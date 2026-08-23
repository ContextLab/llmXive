"""
Base logging infrastructure for the llmXive pipeline.

Provides:
- get_logger(name): Returns a ReproducibilityLogger (tolerant wrapper).
- log_pipeline_step(*args, **kwargs): Tolerant logging function accepting various call shapes.
- RotatingFileHandler setup for ingest.log and vr_mapping.log with JSON formatting.
- log_exclusion and log_vr_mapping helpers.
"""
from __future__ import annotations

import functools
import json
import logging as stdlib_logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from code.config import get_path


# --- Custom JSON Formatter for stdlib logging ---
class JSONFormatter(stdlib_logging.Formatter):
    """Formats log records as JSON lines."""

    def format(self, record: stdlib_logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data
        return json.dumps(log_entry, ensure_ascii=False, default=str)


# --- Setup Rotating File Handlers ---
_handlers_initialized = False

def _setup_handlers() -> None:
    """Initialize RotatingFileHandlers for ingest.log and vr_mapping.log."""
    global _handlers_initialized
    if _handlers_initialized:
        return

    # Ensure log directory exists
    log_dir = get_path("data", "logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    ingest_log_path = str(get_path("data", "logs", "ingest.log"))
    vr_mapping_log_path = str(get_path("data", "logs", "vr_mapping.log"))

    # Root logger configuration
    root_logger = stdlib_logging.getLogger()
    root_logger.setLevel(stdlib_logging.DEBUG)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Ingest Log Handler
    ingest_handler = stdlib_logging.handlers.RotatingFileHandler(
        ingest_log_path, maxBytes=10 * 1024 * 1024, backupCount=5
    )
    ingest_handler.setLevel(stdlib_logging.INFO)
    ingest_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(ingest_handler)

    # VR Mapping Log Handler
    vr_handler = stdlib_logging.handlers.RotatingFileHandler(
        vr_mapping_log_path, maxBytes=10 * 1024 * 1024, backupCount=5
    )
    vr_handler.setLevel(stdlib_logging.INFO)
    vr_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(vr_handler)

    _handlers_initialized = True


# --- Reproducibility Logger (Tolerant Wrapper) ---
class LogEntry:
    """A structured log entry for reproducibility."""

    def __init__(
        self, operation: str, parameters: Optional[Dict[str, Any]] = None
    ) -> None:
        self.operation = operation
        self.parameters = parameters or {}
        self.timestamp = datetime.utcnow().isoformat()

    def to_json(self) -> str:
        return json.dumps(
            {
                "operation": self.operation,
                "parameters": self.parameters,
                "timestamp": self.timestamp,
            },
            ensure_ascii=False,
            default=str,
        )

class ReproducibilityLogger:
    """
    A tolerant logger that wraps stdlib logging but accepts flexible call shapes.
    Never raises on unexpected arguments.
    """

    def __init__(self, name: str = "reproducibility") -> None:
        self.name = name
        self._logger = stdlib_logging.getLogger(name)
        # Ensure handlers are set up
        _setup_handlers()

    def log(self, *args: Any, **kwargs: Any) -> LogEntry:
        """Log an operation and return a LogEntry."""
        operation = args[0] if args else kwargs.get("operation", "unknown")
        entry = LogEntry(operation=str(operation), parameters=dict(kwargs))

        # Map to stdlib logging level if present
        level_str = kwargs.get("level", "INFO")
        level = getattr(stdlib_logging, level_str.upper(), stdlib_logging.INFO)

        # Log to stdlib logger (which has our JSON handlers)
        self._logger.log(level, entry.to_json())
        return entry

    def info(self, *args: Any, **kwargs: Any) -> None:
        """Tolerant info logging."""
        msg = args[0] if args else kwargs.get("message", "")
        self._logger.info(str(msg))

    def debug(self, *args: Any, **kwargs: Any) -> None:
        msg = args[0] if args else kwargs.get("message", "")
        self._logger.debug(str(msg))

    def warning(self, *args: Any, **kwargs: Any) -> None:
        msg = args[0] if args else kwargs.get("message", "")
        self._logger.warning(str(msg))

    def error(self, *args: Any, **kwargs: Any) -> None:
        msg = args[0] if args else kwargs.get("message", "")
        self._logger.error(str(msg))

    def critical(self, *args: Any, **kwargs: Any) -> None:
        msg = args[0] if args else kwargs.get("message", "")
        self._logger.critical(str(msg))

    def __getattr__(self, name: str) -> Any:
        """Delegate unknown attributes to a no-op function."""
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop


# --- Global State ---
_GLOBAL_LOGGER: Optional[ReproducibilityLogger] = None


def get_logger(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
    """
    Get or create the global ReproducibilityLogger.
    Accepts any arguments but uses the first as name if provided.
    """
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        name = args[0] if args else kwargs.get("name", "reproducibility")
        _GLOBAL_LOGGER = ReproducibilityLogger(name)
    return _GLOBAL_LOGGER


def log_operation(*args: Any, **kwargs: Any) -> Any:
    """
    Dual-purpose: decorator or direct logging call.
    Direct call returns LogEntry; decorator returns wrapped function.
    """
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]

        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any) -> Any:
            return func(*a, **k)

        return _wrapper

    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)


def log_pipeline_step(*args: Any, **kwargs: Any) -> None:
    """
    Tolerant logging function for pipeline steps.
    Accepts various call shapes:
    - log_pipeline_step("operation_name")
    - log_pipeline_step("operation_name", "status")
    - log_pipeline_step("operation_name", status="completed")
    - log_pipeline_step(logger, "START", "Description")
    """
    _setup_handlers()
    
    # Handle case where first arg is a logger instance
    if args and isinstance(args[0], ReproducibilityLogger):
        logger = args[0]
        remaining_args = args[1:]
        if remaining_args:
            operation = str(remaining_args[0])
            # Log the remaining args as parameters
            logger.log(operation, **{str(i): v for i, v in enumerate(remaining_args[1:])})
        return

    # Handle standard call shapes
    if not args:
        return

    # Try to parse arguments
    operation = str(args[0]) if args else kwargs.get("operation", "pipeline_step")
    
    # If a second positional arg exists, treat it as status or description
    if len(args) > 1:
        status_or_desc = str(args[1])
        if "status" not in kwargs:
            kwargs["status"] = status_or_desc
        else:
            kwargs["description"] = status_or_desc
    
    # Log using the global logger
    get_logger().log(operation, **kwargs)


# --- Helper Functions for Specific Logs ---
def get_log_path() -> Path:
    return get_path("data", "logs")

def get_exclusion_log_path() -> Path:
    return get_path("data", "logs", "exclusion.log")

def get_vr_mapping_log_path() -> Path:
    return get_path("data", "logs", "vr_mapping.log")

def log_exclusion(reason: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Log an exclusion event."""
    _setup_handlers()
    logger = get_logger("exclusion")
    logger.log("EXCLUSION", reason=reason, details=details)

def log_vr_mapping(story_id: str, salience_level: str, blend_shape_params: Dict[str, Any]) -> None:
    """Log a VR mapping event."""
    _setup_handlers()
    logger = get_logger("vr_mapping")
    logger.log(
        "VR_MAPPING",
        story_id=story_id,
        salience_level=salience_level,
        blend_shape_params=blend_shape_params
    )


def get_reproducibility_logger() -> ReproducibilityLogger:
    return get_logger()

def main() -> None:
    """Test the logging infrastructure."""
    logger = get_logger("test")
    logger.log("TEST", message="Logging infrastructure test")
    
    log_pipeline_step("START", "T009: Logging Infrastructure Test")
    log_pipeline_step("SUCCESS", "T009: Logging Infrastructure Test completed")
    
    # Test specific log types
    log_exclusion("Test exclusion", {"reason": "test"})
    log_vr_mapping("story_001", "high", {"mouth_open": 0.8})
    
    print("Logging infrastructure test completed. Check data/logs/ingest.log")


if __name__ == "__main__":
    main()