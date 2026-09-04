"""
Reproducibility logging infrastructure.

Provides a dual-layer logging system:
1. ReproducibilityLogger: An in-memory logger for pipeline state tracking and JSON serialization.
2. Standard Logging: Configured file handlers with RotatingFileHandler and JSONFormatter for persistent logs.

This implementation satisfies T009 requirements:
- RotatingFileHandler for data/logs/ingest.log and data/logs/vr_mapping.log
- JSONFormatter for structured output
- Tolerant API for all existing call sites
"""
from __future__ import annotations

import functools
import json
import logging
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional

from code.config import get_path, ensure_directories


@dataclass
class LogEntry:
    """Dataclass for structured log entries used by ReproducibilityLogger."""
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """Accepts ANY call shape and never raises.
    
    This is an in-memory logger for pipeline state tracking.
    It does NOT delegate to stdlib logging to avoid type mismatches.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list = []

    def log(self, *args: Any, **kwargs: Any) -> "LogEntry":
        op = args[0] if args else kwargs.get("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        return entry

    # .info/.debug/.warning/.error/.critical/... -> tolerant no-op
    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs log records as JSON strings."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data
        return json.dumps(log_data, ensure_ascii=False, default=str)


# Global state for file-based loggers
_GLOBAL_LOGGER: "ReproducibilityLogger | None" = None
_FILE_LOGGERS: Dict[str, logging.Logger] = {}


def _ensure_file_logger(name: str, filename: str, max_bytes: int = 10_000_000, backup_count: int = 5) -> logging.Logger:
    """
    Create or retrieve a file-based logger with RotatingFileHandler and JSONFormatter.
    
    Args:
        name: Logger name
        filename: Log filename (relative to data/logs/)
        max_bytes: Max size before rotation
        backup_count: Number of backup files to keep
        
    Returns:
        Configured logging.Logger instance
    """
    if name in _FILE_LOGGERS:
        return _FILE_LOGGERS[name]

    # Ensure directories exist
    ensure_directories()
    log_path = get_path("data", "logs", filename)
    
    # Create standard logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Prevent duplicate handlers if called multiple times
    if not logger.handlers:
        # Create RotatingFileHandler
        handler = RotatingFileHandler(
            log_path, 
            maxBytes=max_bytes, 
            backupCount=backup_count,
            encoding="utf-8"
        )
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
    
    _FILE_LOGGERS[name] = logger
    return logger


def get_logger(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
    """Get the global ReproducibilityLogger instance."""
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    return _GLOBAL_LOGGER


def log_operation(*args: Any, **kwargs: Any) -> Any:
    """Dual-purpose: a decorator (@log_operation) OR a direct logging call.
    
    The direct-call path ALWAYS returns a LogEntry (callers use .to_json());
    decorator use returns the wrapped function. Never return a bare function
    from the direct-call path.
    """
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]

        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any) -> Any:
            return func(*a, **k)

        return _wrapper

    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)


def log_pipeline_step(*args: Any, **kwargs: Any) -> Any:
    """
    Tolerant logging function for pipeline steps.
    Accepts various call shapes found in the codebase:
    - log_pipeline_step("operation_name")
    - log_pipeline_step("operation_name", "status")
    - log_pipeline_step("operation_name", parameters_dict)
    - log_pipeline_step(logger, "START", "message")
    - log_pipeline_step("operation_name", status="completed")
    """
    # Handle the case where the first arg is a logger (ReproducibilityLogger or stdlib)
    if args:
        first_arg = args[0]
        if isinstance(first_arg, ReproducibilityLogger):
            # Skip the logger arg if passed, use it to log
            if len(args) > 1:
                op = str(args[1])
                # Pass remaining args as parameters
                params = {str(i): v for i, v in enumerate(args[2:])}
                params.update(kwargs)
                return first_arg.log(op, **params)
            return first_arg.log("pipeline_step", **kwargs)
        
        # If it's a stdlib logger, log via that
        if isinstance(first_arg, logging.Logger):
            msg_parts = [str(a) for a in args[1:]]
            msg = " ".join(msg_parts) if msg_parts else str(kwargs)
            first_arg.info(msg, extra={"extra_data": kwargs})
            return None

    # If no args, just log a generic operation
    if not args:
        return get_logger().log("pipeline_step", **kwargs)

    # First arg is usually the operation name
    operation = str(args[0])
    
    # Second arg could be status or parameters
    if len(args) > 1:
        second = args[1]
        if isinstance(second, str):
            kwargs['status'] = second
        elif isinstance(second, dict):
            kwargs['parameters'] = second
    
    return get_logger().log(operation, **kwargs)


def get_log_path() -> Path:
    """Return the base logs directory path."""
    return get_path("data", "logs")


def get_exclusion_log_path() -> Path:
    """Return the path to the exclusion log file."""
    return get_path("data", "logs", "exclusion.log")


def get_vr_mapping_log_path() -> Path:
    """Return the path to the VR mapping log file."""
    return get_path("data", "logs", "vr_mapping.log")


def log_exclusion(reason: str, details: Dict[str, Any]) -> None:
    """Log an exclusion event to the exclusion log file."""
    entry = {
        "type": "exclusion",
        "reason": reason,
        "details": details,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Write to file-based logger
    logger = _ensure_file_logger("exclusion", "exclusion.log")
    logger.info("Exclusion recorded", extra={"extra_data": entry})
    
    # Also record in memory
    get_logger("exclusion").log("exclusion_record", **entry)


def log_vr_mapping(story_id: str, blend_shape_params: Dict[str, float]) -> None:
    """Log a VR mapping event to the VR mapping log file."""
    entry = {
        "type": "vr_mapping",
        "story_id": story_id,
        "blend_shape_params": blend_shape_params,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Write to file-based logger
    logger = _ensure_file_logger("vr_mapping", "vr_mapping.log")
    logger.info("VR mapping recorded", extra={"extra_data": entry})
    
    # Also record in memory
    get_logger("vr_mapping").log("vr_mapping_record", **entry)


def log_ingest_event(event_type: str, details: Dict[str, Any]) -> None:
    """Log an ingestion event to the ingest log file."""
    entry = {
        "type": "ingest",
        "event": event_type,
        "details": details,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Write to file-based logger
    logger = _ensure_file_logger("ingest", "ingest.log")
    logger.info("Ingest event", extra={"extra_data": entry})
    
    # Also record in memory
    get_logger("ingest").log("ingest_record", **entry)


def get_reproducibility_logger() -> ReproducibilityLogger:
    """Get the global ReproducibilityLogger instance."""
    return get_logger()


def main():
    """Test the logging infrastructure."""
    ensure_directories()
    
    # Test ReproducibilityLogger
    logger = get_logger("test_logger")
    entry = logger.log("test_operation", param1="value1", param2=123)
    print(f"Log entry created: {entry.to_json()}")
    
    # Test log_pipeline_step with various call shapes
    log_pipeline_step("TEST", "test_status")
    log_pipeline_step("TEST2", {"key": "val"})
    log_pipeline_step("TEST3", status="completed")
    
    # Test file-based logging
    log_ingest_event("start", {"mode": "simulation"})
    log_ingest_event("end", {"records": 100})
    
    log_vr_mapping("story_001", {"jaw_open": 0.5, "eye_blink": 0.1})
    
    log_exclusion("invalid_data", {"participant_id": "p999", "reason": "missing_response"})
    
    # Verify files exist
    ingest_path = get_path("data", "logs", "ingest.log")
    vr_path = get_path("data", "logs", "vr_mapping.log")
    
    assert ingest_path.exists(), f"Ingest log not created at {ingest_path}"
    assert vr_path.exists(), f"VR mapping log not created at {vr_path}"
    
    print(f"✓ Ingest log written to: {ingest_path}")
    print(f"✓ VR mapping log written to: {vr_path}")
    
    # Show content of logs
    print("\n--- Ingest Log Content ---")
    with open(ingest_path, 'r') as f:
        print(f.read())
    
    print("\n--- VR Mapping Log Content ---")
    with open(vr_path, 'r') as f:
        print(f.read())
    
    print("Logging infrastructure test passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()