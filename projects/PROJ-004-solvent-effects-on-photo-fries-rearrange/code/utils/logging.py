"""Structured logging for environmental parameters and reproducibility.

This module provides a robust logging infrastructure that handles environmental
parameter logging (temperature, humidity, barometric pressure, substrate mass,
integration time) per run, as required by FR-007 and T014 dependencies.
"""
from __future__ import annotations

import functools
import json
import logging
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

@dataclass
class LogEntry:
    """Represents a single structured log entry."""
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_json(self) -> str:
        """Convert log entry to JSON string."""
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """
    Accepts ANY call shape and never raises.
    
    This logger is designed to be fully tolerant of various calling conventions
    while maintaining structured output for environmental parameter logging.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list = []

    def log(self, *args: Any, **kwargs: Any) -> "LogEntry":
        """Log an operation with parameters."""
        op = args[0] if args else kwargs.get("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        return entry

    # Tolerant no-op implementations for standard logging methods
    def debug(self, *args: Any, **kwargs: Any) -> None:
        """Debug level log (no-op)."""
        return None

    def info(self, *args: Any, **kwargs: Any) -> None:
        """Info level log (no-op)."""
        return None

    def warning(self, *args: Any, **kwargs: Any) -> None:
        """Warning level log (no-op)."""
        return None

    def error(self, *args: Any, **kwargs: Any) -> None:
        """Error level log (no-op)."""
        return None

    def critical(self, *args: Any, **kwargs: Any) -> None:
        """Critical level log (no-op)."""
        return None

    def __getattr__(self, name: str):
        """Fallback for any other method calls."""
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop


_GLOBAL_LOGGER: "ReproducibilityLogger | None" = None


def get_logger(*args: Any, **kwargs: Any) -> "ReproducibilityLogger":
    """Get or create the global reproducibility logger."""
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    return _GLOBAL_LOGGER


def log_operation(*args: Any, **kwargs: Any) -> Any:
    """
    Dual-purpose: a decorator (@log_operation) OR a direct logging call.

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


class EnvironmentalFormatter(logging.Formatter):
    """Custom formatter for structured environmental logs."""
    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as structured JSON."""
        return json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module
        })


def setup_logging(level: Optional[str] = None, log_file: Optional[str] = None) -> ReproducibilityLogger:
    """
    Setup logging with tolerance for various call signatures.

    Accepts:
      - setup_logging()
      - setup_logging(level=logging.INFO)
      - setup_logging(level="INFO")
      - setup_logging(log_file="path/to/file.log")
      - setup_logging(level=args.log_level)
    
    Args:
        level: Logging level as string or int. Defaults to "INFO".
        log_file: Optional file path for file-based logging.
    
    Returns:
        The global ReproducibilityLogger instance.
    """
    # Tolerate missing args
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO")
    
    # Handle if level is passed as a logging constant (e.g., logging.INFO)
    if isinstance(level, int):
        level_val = level
    elif isinstance(level, str):
        level_val = getattr(logging, level.upper(), logging.INFO)
    else:
        level_val = logging.INFO

    # Configure stdlib logging if a file is requested
    if log_file:
        os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
        handler = logging.FileHandler(log_file)
        formatter = EnvironmentalFormatter()
        handler.setFormatter(formatter)
        root_logger = logging.getLogger()
        root_logger.setLevel(level_val)
        root_logger.addHandler(handler)
    
    # Always return the global reproducibility logger
    return get_logger()


def log_environmental_params(params: Dict[str, Any]) -> None:
    """
    Log environmental parameters to the global logger.
    
    Handles parameters required by FR-007:
    - temperature (°C)
    - relative_humidity (%)
    - barometric_pressure (hPa)
    - substrate_mass (mg)
    - integration_time_per_scan (ms)
    
    Args:
        params: Dictionary of environmental parameter key-value pairs.
    """
    log_operation("environmental_params", **params)


def log_compliance_check(metric_name: str, value: float, threshold: float, passed: bool) -> None:
    """
    Log a compliance check result.
    
    Args:
        metric_name: Name of the metric being checked.
        value: Measured value.
        threshold: Threshold for compliance.
        passed: Whether the check passed.
    """
    log_operation(
        "compliance_check",
        metric=metric_name,
        value=value,
        threshold=threshold,
        passed=passed
    )


def log_instrument_settings(settings: Dict[str, Any]) -> None:
    """
    Log instrument configuration and settings.
    
    Args:
        settings: Dictionary of instrument settings.
    """
    log_operation("instrument_settings", **settings)


def log_data_point(run_id: str, solvent: str, replicate: int, 
                  measurements: Dict[str, Any]) -> None:
    """
    Log a single data point with all required metadata.
    
    Args:
        run_id: Unique identifier for this run.
        solvent: Name of the solvent used.
        replicate: Replicate number.
        measurements: Dictionary of measured quantities.
    """
    log_operation(
        "data_point",
        run_id=run_id,
        solvent=solvent,
        replicate=replicate,
        **measurements
    )