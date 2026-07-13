"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
import logging as stdlib_logging
import sys
import time
import warnings
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union


@dataclass
class LogEntry:
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    level: str = "INFO"
    message: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """Accepts ANY call shape and never raises.

    Do NOT subclass or delegate to the stdlib ``logging`` module: its
    ``log(level, msg)`` needs an integer level and has no ``to_json`` — that is
    exactly what keeps breaking. This logger is self-contained.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list = []
        self._stdlib_logger = stdlib_logging.getLogger(self.name)
        # Configure stdlib logger if not already configured
        if not self._stdlib_logger.handlers:
            handler = stdlib_logging.StreamHandler(sys.stdout)
            formatter = stdlib_logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self._stdlib_logger.addHandler(handler)
            self._stdlib_logger.setLevel(stdlib_logging.INFO)

    def log(self, *args: Any, **kwargs: Any) -> "LogEntry":
        op = args[0] if args else kwargs.get("operation", "")
        msg = args[1] if len(args) > 1 else kwargs.get("message", "")
        level = args[2] if len(args) > 2 else kwargs.get("level", "INFO")
        
        entry = LogEntry(
            operation=str(op),
            parameters=dict(kwargs),
            level=str(level),
            message=str(msg)
        )
        self.entries.append(entry)
        
        # Also log to stdlib for immediate visibility
        level_map = {
            "DEBUG": stdlib_logging.DEBUG,
            "INFO": stdlib_logging.INFO,
            "WARNING": stdlib_logging.WARNING,
            "ERROR": stdlib_logging.ERROR,
            "CRITICAL": stdlib_logging.CRITICAL
        }
        std_level = level_map.get(str(level).upper(), stdlib_logging.INFO)
        if msg:
            self._stdlib_logger.log(std_level, msg)
        return entry

    # .info/.debug/.warning/.error/.critical/... -> tolerant forwarding
    def __getattr__(self, name: str):
        def _forward(*args: Any, **kwargs: Any) -> None:
            # Forward to stdlib logger
            level_map = {
                "debug": stdlib_logging.DEBUG,
                "info": stdlib_logging.INFO,
                "warning": stdlib_logging.WARNING,
                "error": stdlib_logging.ERROR,
                "critical": stdlib_logging.CRITICAL
            }
            std_level = level_map.get(name, stdlib_logging.INFO)
            if args:
                self._stdlib_logger.log(std_level, args[0])
            elif "msg" in kwargs:
                self._stdlib_logger.log(std_level, kwargs["msg"])
        return _forward


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


def retry_on_failure(
    max_attempts: int = 3,
    delay: Optional[float] = None,
    delay_seconds: Optional[float] = None,
    logger: Optional[Any] = None,
    exceptions: Optional[tuple] = None
) -> Callable:
    """Decorator to retry a function on failure.
    
    Accepts both `delay` and `delay_seconds` for compatibility.
    """
    if exceptions is None:
        exceptions = (Exception,)
    
    # Normalize delay parameter
    actual_delay = delay if delay is not None else (delay_seconds if delay_seconds is not None else 1.0)
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(actual_delay)
                        if logger:
                            logger.warning(
                                f"Retry {attempt + 1}/{max_attempts} for {func.__name__}: {str(e)}"
                            )
            raise last_exception
        return wrapper
    return decorator


class WarningContext:
    """Context manager to capture warnings."""
    
    def __init__(self) -> None:
        self.warnings: List[Dict[str, Any]] = []
        self._original_showwarning = None
    
    def __enter__(self) -> "WarningContext":
        def custom_showwarning(message, category, filename, lineno, file=None, line=None):
            self.warnings.append({
                "message": str(message),
                "category": category.__name__,
                "filename": filename,
                "lineno": lineno
            })
            # Also print to stderr
            if file is None:
                file = sys.stderr
            file.write(f"{category.__name__}: {message}\n")
        
        self._original_showwarning = warnings.showwarning
        warnings.showwarning = custom_showwarning
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._original_showwarning:
            warnings.showwarning = self._original_showwarning


def capture_warning() -> WarningContext:
    """Factory to create a WarningContext."""
    return WarningContext()


def log_retry_attempts(
    func_name: str,
    attempt: int,
    max_attempts: int,
    error: str,
    logger: Optional[Any] = None
) -> None:
    """Log retry attempt details."""
    if logger:
        logger.warning(
            f"Attempt {attempt}/{max_attempts} failed for {func_name}: {error}"
        )


def setup_logging(
    level: str = "INFO",
    format_string: Optional[str] = None
) -> None:
    """Setup standard logging configuration."""
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    stdlib_logging.basicConfig(
        level=getattr(stdlib_logging, level.upper(), stdlib_logging.INFO),
        format=format_string
    )


def export_warning_log(
    context: WarningContext,
    output_path: str
) -> None:
    """Export captured warnings to a JSON file."""
    import os
    from pathlib import Path
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(context.warnings, f, indent=2, default=str)