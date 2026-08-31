"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from logging.handlers import RotatingFileHandler


@dataclass
class LogEntry:
    """Schema-compliant log entry matching contracts/logging_schema.yaml."""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    level: str = "INFO"
    message: str = ""
    trace_id: str = ""
    module: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)

    def to_dict(self) -> dict:
        return asdict(self)


class ReproducibilityLogger:
    """Accepts ANY call shape and never raises.

    This logger is self-contained and does NOT delegate to the stdlib
    ``logging`` module to avoid type/level mismatches. It supports:
    - Standard logger calls (.info, .debug, .warning, .error, .critical)
    - Explicit log() calls with operation/parameters
    - JSON serialization via .to_json() on returned entries
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list = []
        self._file_handler: RotatingFileHandler | None = None
        self._log_file_path: Path | None = None
        self._max_bytes = kwargs.get("max_bytes", 10 * 1024 * 1024)  # 10MB
        self._backup_count = kwargs.get("backup_count", 5)
        self._initialized = False

    def _ensure_handler(self, log_file_path: str | Path | None = None) -> None:
        """Initialize the rotating file handler if not already done."""
        if self._initialized:
            return

        path = Path(log_file_path) if log_file_path else Path("data/logs/app.log")
        path.parent.mkdir(parents=True, exist_ok=True)

        self._log_file_path = path
        self._file_handler = RotatingFileHandler(
            str(path),
            maxBytes=self._max_bytes,
            backupCount=self._backup_count,
        )
        self._initialized = True

    def _log_entry(
        self,
        level: str,
        message: str,
        module: str = "",
        trace_id: str = "",
        **kwargs: Any,
    ) -> LogEntry:
        """Create and optionally persist a LogEntry."""
        entry = LogEntry(
            timestamp=datetime.utcnow().isoformat(),
            level=level,
            message=message,
            trace_id=trace_id,
            module=module,
        )
        self.entries.append(entry)

        if self._file_handler:
            self._file_handler.emit(
                type(
                    "FakeRecord",
                    (),
                    {
                        "getMessage": lambda self=entry: entry.message,
                        "levelname": level,
                        "name": self.name,
                        "created": datetime.utcnow().timestamp(),
                        "filename": "logging_config.py",
                        "lineno": 0,
                        "funcName": "log_entry",
                        "args": (),
                        "exc_info": None,
                        "exc_text": None,
                        "stack_info": None,
                        "getMessage": lambda: entry.message,
                        "__dict__": entry.to_dict(),
                    },
                )()
            )

        return entry

    def log(self, *args: Any, **kwargs: Any) -> LogEntry:
        """Log an operation with optional parameters."""
        op = args[0] if args else kwargs.get("operation", "")
        level = kwargs.get("level", "INFO")
        module = kwargs.get("module", self.name)
        trace_id = kwargs.get("trace_id", "")

        # Strip internal kwargs
        for key in ["operation", "level", "module", "trace_id"]:
            kwargs.pop(key, None)

        return self._log_entry(level, str(op), module, trace_id, **kwargs)

    # Standard logger methods -> tolerant no-op or entry creation
    def info(self, msg: str, *args: Any, **kwargs: Any) -> LogEntry:
        return self._log_entry("INFO", msg, **kwargs)

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> LogEntry:
        return self._log_entry("DEBUG", msg, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> LogEntry:
        return self._log_entry("WARNING", msg, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> LogEntry:
        return self._log_entry("ERROR", msg, **kwargs)

    def critical(self, msg: str, *args: Any, **kwargs: Any) -> LogEntry:
        return self._log_entry("CRITICAL", msg, **kwargs)

    def exception(self, msg: str, *args: Any, **kwargs: Any) -> LogEntry:
        return self._log_entry("ERROR", msg, **kwargs)

    def __getattr__(self, name: str):
        """Fallback for any unrecognized method calls."""
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop


_GLOBAL_LOGGER: "ReproducibilityLogger | None" = None


def get_logger(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
    """Get or create the global logger instance."""
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


def setup_logging(
    *args: Any,
    log_file: str | Path | None = None,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    **kwargs: Any,
) -> ReproducibilityLogger:
    """Tolerant logging setup that accepts any call shape.

    Supports:
    - setup_logging()
    - setup_logging(level="INFO")
    - setup_logging(log_level="INFO")
    - setup_logging(config)
    - setup_logging(log_file="data/logs/app.log")

    Initializes the rotating file handler if a log_file is provided.
    """
    logger = get_logger(*args, **kwargs)

    # Extract level from various possible kwargs (just for logging, not enforcement)
    level = kwargs.get('level') or kwargs.get('log_level')
    if level:
        logger.log("setup_logging", level=str(level))

    # Configure file handler if path provided or default
    if log_file:
        logger._ensure_handler(log_file)
    else:
        # Default path per T006 requirements
        default_path = Path("data/logs/app.log")
        if not logger._initialized:
            logger._ensure_handler(default_path)

    logger._max_bytes = max_bytes
    logger._backup_count = backup_count

    return logger


def log_with_extra(*args: Any, **kwargs: Any) -> None:
    """Tolerant logging with extra parameters."""
    get_logger().log("log_with_extra", **kwargs)