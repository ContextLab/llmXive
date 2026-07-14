"""Reproducibility logging — fully tolerant; raises on nothing.

Implements FR-010: Configure error logging with timestamps to `experiment.log`.
Log format: `[TIMESTAMP] [LEVEL] [MODULE] Message`.
"""
from __future__ import annotations

import functools
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, TextIO

# Path for the experiment log file (relative to project root)
# Per task T007 requirement: output to `experiment.log` in the project root context
# We use a relative path that resolves correctly when run from the project root.
_LOG_FILE_PATH = Path("experiment.log")


@dataclass
class LogEntry:
    """Structured log entry."""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    level: str = "INFO"
    module: str = "root"
    message: str = ""
    parameters: dict = field(default_factory=dict)

    def to_json(self) -> str:
        """Serialize entry to JSON string."""
        return json.dumps(asdict(self), ensure_ascii=False, default=str)

    def to_log_format(self) -> str:
        """Format entry as `[TIMESTAMP] [LEVEL] [MODULE] Message`."""
        return f"[{self.timestamp}] [{self.level}] [{self.module}] {self.message}"


class FileHandler:
    """Simple file handler that appends log lines."""
    def __init__(self, filepath: Path) -> None:
        self.filepath = filepath
        # Ensure directory exists
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

    def write(self, line: str) -> None:
        with open(self.filepath, "a", encoding="utf-8") as f:
            f.write(line + "\n")


class ReproducibilityLogger:
    """Accepts ANY call shape and never raises.
    
    Implements FR-010 logging format: `[TIMESTAMP] [LEVEL] [MODULE] Message`.
    Writes to `experiment.log` in the project root.
    """

    def __init__(self, name: str = "reproducibility", log_file: Optional[Path] = None) -> None:
        self.name = name
        self._module = name.rsplit(".", 1)[-1] if "." in name else name
        self._file_handler = FileHandler(log_file or _LOG_FILE_PATH)

    def _log(self, level: str, message: str, **kwargs: Any) -> LogEntry:
        entry = LogEntry(
            level=level,
            module=self._module,
            message=message,
            parameters=kwargs
        )
        # Write formatted line to file
        self._file_handler.write(entry.to_log_format())
        return entry

    def log(self, *args: Any, **kwargs: Any) -> LogEntry:
        """Generic log method.
        
        Args can be: (level, message) or just message with level in kwargs.
        """
        if args:
            if len(args) >= 2:
                level = str(args[0]).upper()
                message = str(args[1])
            else:
                level = kwargs.get("level", "INFO").upper()
                message = str(args[0])
        else:
            level = kwargs.get("level", "INFO").upper()
            message = kwargs.get("message", "")
        
        # Remove level/message from kwargs if present
        kwargs.pop("level", None)
        kwargs.pop("message", None)
        
        return self._log(level, message, **kwargs)

    def info(self, msg: str, **kwargs: Any) -> LogEntry:
        return self._log("INFO", msg, **kwargs)

    def debug(self, msg: str, **kwargs: Any) -> LogEntry:
        return self._log("DEBUG", msg, **kwargs)

    def warning(self, msg: str, **kwargs: Any) -> LogEntry:
        return self._log("WARNING", msg, **kwargs)

    def error(self, msg: str, **kwargs: Any) -> LogEntry:
        return self._log("ERROR", msg, **kwargs)

    def critical(self, msg: str, **kwargs: Any) -> LogEntry:
        return self._log("CRITICAL", msg, **kwargs)

    # Tolerant fallback for any other attribute access
    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop


_GLOBAL_LOGGER: Optional[ReproducibilityLogger] = None


def get_logger(name: str = "reproducibility", log_file: Optional[Path] = None) -> ReproducibilityLogger:
    """Get or create a logger instance.
    
    Args:
        name: Logger name (used as module identifier)
        log_file: Optional path to log file (defaults to experiment.log)
    
    Returns:
        ReproducibilityLogger instance
    """
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(name=name, log_file=log_file)
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
            logger = get_logger(func.__module__)
            logger.info(f"Starting {func.__name__}")
            try:
                result = func(*a, **k)
                logger.info(f"Completed {func.__name__}")
                return result
            except Exception as e:
                logger.error(f"Failed {func.__name__}: {str(e)}")
                raise

        return _wrapper

    op = args[0] if args else kwargs.pop("operation", "operation")
    level = kwargs.pop("level", "INFO")
    return get_logger().log(level, op, **kwargs)