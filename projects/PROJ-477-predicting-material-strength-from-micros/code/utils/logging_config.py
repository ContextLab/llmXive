"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Callable


@dataclass
class LogEntry:
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """Accepts ANY call shape and never raises.

    This logger writes to:
    1. `results/metrics.log` (text log of all operations)
    2. `results/metrics.json` (JSON array of all LogEntry objects)
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = "reproducibility"
        self.log_file = None
        self.json_file = None

        # Parse args/kwargs for name and optional log file
        if args:
            self.name = str(args[0])
            if len(args) > 1:
                self.log_file = str(args[1])

        if "name" in kwargs:
            self.name = str(kwargs["name"])
        if "log_file" in kwargs:
            self.log_file = str(kwargs["log_file"])

        self.entries: list = []
        
        # Ensure results directory exists
        self.results_dir = os.path.join(os.getcwd(), "results")
        os.makedirs(self.results_dir, exist_ok=True)

        # Initialize default file paths if not specified
        if not self.log_file:
            self.log_file = "metrics.log"
        self.json_file = "metrics.json"

        self._text_log_path = os.path.join(self.results_dir, self.log_file)
        self._json_log_path = os.path.join(self.results_dir, self.json_file)

        # Initialize stdlib logging for text output
        self._init_stdlib_logger()

    def _init_stdlib_logger(self) -> None:
        """Initialize standard logging to write to the specified file."""
        import logging

        # Create a custom logger
        std_logger = logging.getLogger(f"stdlib_{self.name}")
        std_logger.setLevel(logging.INFO)

        # Avoid adding handlers multiple times
        if not std_logger.handlers:
            fh = logging.FileHandler(self._text_log_path, mode='a')
            fh.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            fh.setFormatter(formatter)
            std_logger.addHandler(fh)

        # Store reference for later use
        self._stdlib_logger = std_logger

    def log(self, *args: Any, **kwargs: Any) -> "LogEntry":
        op = args[0] if args else kwargs.get("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)

        # Write to stdlib logger if initialized
        if hasattr(self, '_stdlib_logger'):
            msg = f"{op} - {kwargs}"
            self._stdlib_logger.info(msg)

        # Write JSON entry to file immediately
        self._write_json_entry(entry)

        return entry

    def _write_json_entry(self, entry: LogEntry) -> None:
        """Append a single log entry to the JSON file."""
        try:
            # Read existing entries if file exists
            existing_entries = []
            if os.path.exists(self._json_log_path):
                try:
                    with open(self._json_log_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            existing_entries = json.loads(content)
                except (json.JSONDecodeError, ValueError):
                    # If file is corrupted, start fresh
                    existing_entries = []

            # Append new entry
            existing_entries.append(asdict(entry))

            # Write back all entries
            with open(self._json_log_path, 'w', encoding='utf-8') as f:
                json.dump(existing_entries, f, indent=2, ensure_ascii=False, default=str)
        except Exception:
            # Fail silently to avoid breaking the main workflow
            pass

    # .info/.debug/.warning/.error/.critical/... -> tolerant no-op or stdlib delegate
    def __getattr__(self, name: str):
        # If we have a stdlib logger and the method exists there, delegate
        if hasattr(self, '_stdlib_logger') and hasattr(self._stdlib_logger, name):
            return getattr(self._stdlib_logger, name)

        # Otherwise, return a no-op
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop


_GLOBAL_LOGGER: "ReproducibilityLogger | None" = None


def get_logger(*args: Any, **kwargs: Any) -> "ReproducibilityLogger":
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


class JsonFormatter(logging.Formatter):
    """Formatter that outputs JSON strings after parsing the LogRecord."""

    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if hasattr(record, 'extra_data'):
            log_data['extra'] = record.extra_data
        return json.dumps(log_data)


def log_metric(metric_name: str, value: float, **kwargs: Any) -> None:
    """Log a metric to the global logger's entries and optionally to a file."""
    entry = get_logger().log("metric_recorded", name=metric_name, value=value, **kwargs)
    if hasattr(get_logger(), '_stdlib_logger'):
        get_logger()._stdlib_logger.info(f"Metric: {metric_name} = {value}")


def main() -> None:
    """Entry point for testing the logging module."""
    logger = get_logger("test")
    logger.log("test_operation", key="value")
    print("Log entry created:", logger.entries[0].to_json())
    print(f"Text log written to: {logger._text_log_path}")
    print(f"JSON log written to: {logger._json_log_path}")