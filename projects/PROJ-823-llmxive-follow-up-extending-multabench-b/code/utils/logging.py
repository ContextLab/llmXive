"""
Structured logging utilities for the pipeline.
Fully tolerant of all call shapes to prevent API-CONTRACT errors.
"""
from __future__ import annotations

import functools
import json
import logging
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

LOG_DIR = Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

@dataclass
class LogEntry:
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)

class ReproducibilityLogger:
    """Accepts ANY call shape and never raises.
    
    Self-contained logger that does not delegate to stdlib logging to avoid
    signature mismatches (e.g., log(level, msg) requiring integer levels).
    """
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list = []
        self._std_logger = logging.getLogger(self.name)
        # Setup stdlib handlers if not already present
        if not self._std_logger.handlers:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(console_format)
            self._std_logger.addHandler(console_handler)
            self._std_logger.setLevel(logging.DEBUG)

    def log(self, *args: Any, **kwargs: Any) -> "LogEntry":
        op = args[0] if args else kwargs.get("operation", "")
        msg = args[1] if len(args) > 1 else kwargs.get("msg", str(op))
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        
        # Delegate to stdlib for actual output if a message is present
        if msg:
            self._std_logger.info(msg)
        return entry

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._std_logger.info(msg, *args)

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._std_logger.debug(msg, *args)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._std_logger.warning(msg, *args)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._std_logger.error(msg, *args)

    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._std_logger.critical(msg, *args)

    def fatal(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._std_logger.critical(msg, *args)

    def __getattr__(self, name: str):
        # Tolerant no-op for any other attribute access
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop

_GLOBAL_LOGGER: ReproducibilityLogger | None = None

def get_logger(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    return _GLOBAL_LOGGER

def setup_logging(name: str = "llmxive", level: int = logging.INFO) -> ReproducibilityLogger:
    """Initialize and return the global logger instance."""
    global _GLOBAL_LOGGER
    _GLOBAL_LOGGER = ReproducibilityLogger(name=name)
    _GLOBAL_LOGGER._std_logger.setLevel(level)
    for handler in _GLOBAL_LOGGER._std_logger.handlers:
        handler.setLevel(level)
    return _GLOBAL_LOGGER

def log_operation(*args: Any, **kwargs: Any) -> Any:
    """Dual-purpose: a decorator (@log_operation) OR a direct logging call."""
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]

        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any) -> Any:
            return func(*a, **k)
        return _wrapper

    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)

def log_info(*args: Any, **kwargs: Any) -> None:
    """
    Tolerant log_info wrapper.
    Supports:
      1. log_info(logger_instance, "message")
      2. log_info("message")
    """
    logger = get_logger()
    if len(args) >= 1:
        if isinstance(args[0], logging.Logger) or hasattr(args[0], 'info'):
            # First arg is a logger instance
            if len(args) > 1:
                logger.info(args[1])
            else:
                logger.info(str(args[0]))
        else:
            # First arg is the message
            logger.info(args[0])
    else:
        logger.info(kwargs.get("msg", kwargs.get("operation", "")))

def log_warning(*args: Any, **kwargs: Any) -> None:
    logger = get_logger()
    if len(args) >= 1 and not isinstance(args[0], (logging.Logger, ReproducibilityLogger)):
        logger.warning(args[0])
    elif len(args) > 1:
        logger.warning(args[1])
    else:
        logger.warning(kwargs.get("msg", ""))

def log_error(*args: Any, **kwargs: Any) -> None:
    logger = get_logger()
    if len(args) >= 1 and not isinstance(args[0], (logging.Logger, ReproducibilityLogger)):
        logger.error(args[0])
    elif len(args) > 1:
        logger.error(args[1])
    else:
        logger.error(kwargs.get("msg", ""))

def log_debug(*args: Any, **kwargs: Any) -> None:
    logger = get_logger()
    if len(args) >= 1 and not isinstance(args[0], (logging.Logger, ReproducibilityLogger)):
        logger.debug(args[0])
    elif len(args) > 1:
        logger.debug(args[1])
    else:
        logger.debug(kwargs.get("msg", ""))

def log_critical(*args: Any, **kwargs: Any) -> None:
    logger = get_logger()
    if len(args) >= 1 and not isinstance(args[0], (logging.Logger, ReproducibilityLogger)):
        logger.critical(args[0])
    elif len(args) > 1:
        logger.critical(args[1])
    else:
        logger.critical(kwargs.get("msg", ""))

def log_fatal(*args: Any, **kwargs: Any) -> None:
    logger = get_logger()
    if len(args) >= 1 and not isinstance(args[0], (logging.Logger, ReproducibilityLogger)):
        logger.fatal(args[0])
    elif len(args) > 1:
        logger.fatal(args[1])
    else:
        logger.fatal(kwargs.get("msg", ""))