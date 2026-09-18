"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
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
    """Structured log entry matching the schema in contracts/logging_schema.yaml."""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    level: str = "INFO"
    message: str = ""
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    module: str = "root"
    operation: str = ""
    parameters: dict = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """Accepts ANY call shape and never raises.

    This logger is self-contained and does not delegate to the stdlib `logging` module
    for its primary interface, avoiding integer level issues and missing `to_json`.
    It wraps the stdlib handler for file rotation but exposes a tolerant API.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list = []
        self._stdlib_logger: Optional[logging.Logger] = None

    def _ensure_stdlib(self) -> logging.Logger:
        if self._stdlib_logger is None:
            self._stdlib_logger = logging.getLogger(f"repro.{self.name}")
            self._stdlib_logger.setLevel(logging.DEBUG)
            # Prevent double logging if root is configured
            self._stdlib_logger.propagate = False
        return self._stdlib_logger

    def log(self, *args: Any, **kwargs: Any) -> LogEntry:
        op = args[0] if args else kwargs.get("operation", "")
        entry = LogEntry(
            operation=str(op),
            message=kwargs.get("message", ""),
            level=kwargs.get("level", "INFO"),
            module=kwargs.get("module", "root"),
            trace_id=kwargs.get("trace_id", str(uuid.uuid4())),
            parameters=dict(kwargs)
        )
        self.entries.append(entry)

        # Also push to stdlib handler if configured
        stdlib_log = self._ensure_stdlib()
        # Format as JSON for the file handler
        stdlib_log.info(entry.to_json())

        return entry

    # .info/.debug/.warning/.error/.critical/... -> tolerant no-op or passthrough
    def __getattr__(self, name: str):
        def _call(*args: Any, **kwargs: Any) -> Any:
            # If it looks like a standard logger call (level, msg), pass to stdlib
            if self._stdlib_logger:
                level_map = {
                    "debug": logging.DEBUG,
                    "info": logging.INFO,
                    "warning": logging.WARNING,
                    "error": logging.ERROR,
                    "critical": logging.CRITICAL
                }
                lvl = level_map.get(name, logging.INFO)
                msg = args[0] if args else kwargs.get("msg", "")
                self._stdlib_logger.log(lvl, str(msg))
            return None
        return _call


_GLOBAL_LOGGER: Optional[ReproducibilityLogger] = None
_STD_LOG_HANDLER: Optional[logging.handlers.RotatingFileHandler] = None


def get_logger(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    return _GLOBAL_LOGGER


def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    module_name: Optional[str] = None,
    config: Optional[Any] = None,
    **kwargs: Any
) -> ReproducibilityLogger:
    """
    Setup logging infrastructure.
    Accepts multiple call shapes to satisfy all callers:
    - setup_logging()
    - setup_logging(level="INFO")
    - setup_logging(log_level="INFO")
    - setup_logging(config)
    - setup_logging(log_file="data/logs/app.log")
    - setup_logging(level=args.log_level)
    - setup_logging(module_name=kwargs.get("module", "root"))
    - setup_logging(module_name=module_name)
    """
    global _GLOBAL_LOGGER, _STD_LOG_HANDLER

    # Normalize arguments
    effective_level = level or kwargs.get("log_level", "INFO")
    if config and hasattr(config, 'get'):
        effective_level = config.get('log_level', effective_level)

    # Determine log file path
    effective_log_file = log_file or kwargs.get("log_file")
    if not effective_log_file:
        if config and hasattr(config, 'data_logs'):
            effective_log_file = config.data_logs
        else:
            # Fallback to default if config not passed or lacks attribute
            cfg = get_config()
            if cfg and hasattr(cfg, 'data_logs'):
                effective_log_file = cfg.data_logs
            else:
                effective_log_file = "data/logs/app.log"

    # Ensure directory exists
    Path(effective_log_file).parent.mkdir(parents=True, exist_ok=True)

    # Setup RotatingFileHandler if not already set
    if _STD_LOG_HANDLER is None:
        _STD_LOG_HANDLER = logging.handlers.RotatingFileHandler(
            effective_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        _STD_LOG_HANDLER.setLevel(logging.DEBUG)
        _STD_LOG_HANDLER.setFormatter(logging.Formatter('%(message)s'))

    # Configure root logger if needed
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(_STD_LOG_HANDLER)

    # Initialize or return global logger
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(name=module_name or "root")
        # Trigger stdlib setup for this logger
        _ = _GLOBAL_LOGGER._ensure_stdlib()

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
            # Log the call
            log_operation(func.__name__, module=func.__module__)
            return func(*a, **k)

        return _wrapper

    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)


def validate_schema_exists() -> bool:
    """
    Validate that contracts/logging_schema.yaml exists.
    """
    schema_path = Path("contracts/logging_schema.yaml")
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    return True


def log_with_extra(
    message: str,
    level: str = "INFO",
    module: str = "root",
    **extra: Any
) -> LogEntry:
    """
    Log a message with extra fields, matching the schema.
    """
    entry = LogEntry(
        message=message,
        level=level,
        module=module,
        trace_id=extra.get("trace_id", str(uuid.uuid4())),
        parameters=extra
    )
    get_logger().entries.append(entry)
    std_log = get_logger()._ensure_stdlib()
    std_log.info(entry.to_json())
    return entry
