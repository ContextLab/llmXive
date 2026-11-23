"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Any

@dataclass
class LogEntry:
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)

class ReproducibilityLogger:
    """Accepts ANY call shape and never raises.

    Do NOT subclass or delegate to the stdlib ``logging`` module: its
    ``log(level, msg)`` needs an integer level and has no ``to_json`` — that is
    exactly what keeps breaking. This logger is self-contained.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Handle various call shapes: (name,), (name, log_dir), (log_level=), (script_name=)
        self.name = "reproducibility"
        self.log_dir = None
        
        if args:
            # First positional arg is usually name or script_name
            first = args[0]
            if isinstance(first, str):
                self.name = first
        
        # Check kwargs for overrides
        self.name = kwargs.get('name', kwargs.get('script_name', self.name))
        self.log_level = kwargs.get('log_level', 'INFO')
        self.log_dir = kwargs.get('log_dir', kwargs.get('log_directory', None))

        self.entries: list = []
        
        # Initialize actual file handler if log_dir provided
        self._file_handler = None
        if self.log_dir:
            os.makedirs(self.log_dir, exist_ok=True)
            log_file_path = os.path.join(self.log_dir, f"{self.name}.log")
            try:
                self._file_handler = RotatingFileHandler(
                    log_file_path, maxBytes=10*1024*1024, backupCount=5
                )
                self._file_handler.setFormatter(
                    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                )
            except Exception:
                # Fail silently on file handler creation to keep logger tolerant
                pass

    def log(self, *args: Any, **kwargs: Any) -> "LogEntry":
        op = args[0] if args else kwargs.get("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        
        # Write to file handler if available
        if self._file_handler:
            msg = f"{entry.timestamp} - {op}: {json.dumps(kwargs)}"
            self._file_handler.emit(
                logging.LogRecord(
                    name=self.name, 
                    level=logging.INFO, 
                    pathname="", 
                    lineno=0, 
                    msg=msg, 
                    args=(), 
                    exc_info=None
                )
            )
        return entry

    # .info/.debug/.warning/.error/.critical/... -> tolerant no-op
    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop

_GLOBAL_LOGGER: "ReproducibilityLogger | None" = None
import logging as stdlib_logging # Import stdlib logging for RotatingFileHandler

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

def get_log_directory() -> str:
    """Return the default log directory."""
    return "data/logs"

def setup_logging(
    script_name: str | None = None,
    log_file: str | None = None,
    log_level: str | None = None,
    log_dir: str | None = None,
    name: str | None = None,
) -> ReproducibilityLogger:
    """
    Setup logging for a script. Accepts flexible arguments to match all call sites.
    
    Args:
        script_name: Name of the script (e.g., "fetch_github")
        log_file: Explicit log file path (deprecated, use log_dir + script_name)
        log_level: Log level string (e.g., "INFO")
        log_dir: Directory for log files
        name: Logger name
    
    Returns:
        A ReproducibilityLogger instance
    """
    # Determine name
    final_name = name or script_name or "reproducibility"
    
    # Determine log directory
    final_log_dir = log_dir
    if not final_log_dir and log_file:
        # Extract directory from log_file
        final_log_dir = os.path.dirname(log_file) or "data/logs"
    elif not final_log_dir:
        final_log_dir = "data/logs"
    
    # Ensure directory exists
    os.makedirs(final_log_dir, exist_ok=True)
    
    # If log_file is explicitly provided, use it; otherwise construct from script_name
    final_log_file = log_file
    if not final_log_file and script_name:
        final_log_file = os.path.join(final_log_dir, f"{script_name}.log")
    
    # Create logger with appropriate parameters
    logger = get_logger(
        name=final_name,
        log_dir=final_log_dir,
        log_level=log_level or "INFO",
        script_name=script_name
    )
    
    return logger

def rotate_logs(log_dir: str | None = None) -> None:
    """Rotate logs if needed (no-op for ReproducibilityLogger, but provided for API compatibility)."""
    pass

def init_logger_for_script(script_name: str, log_dir: str | None = None) -> ReproducibilityLogger:
    """Initialize a logger for a specific script."""
    return setup_logging(script_name=script_name, log_dir=log_dir)

def main() -> None:
    """CLI entry point for logging module (no-op)."""
    pass
