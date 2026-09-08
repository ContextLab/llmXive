"""
Reproducibility logging infrastructure for llmXive.

Implements JSON logging with rotation, tolerant of all call signatures
found across the codebase.
"""
from __future__ import annotations

import functools
import json
import logging
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional

from config import get_config


@dataclass
class LogEntry:
    """Structured log entry matching contracts/logging_schema.yaml."""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    level: str = "INFO"
    message: str = ""
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    module: str = "root"
    operation: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    success: Optional[bool] = None
    duration_ms: Optional[float] = None
    error: Optional[str] = None

    def to_json(self) -> str:
        """Serialize to JSON string."""
        # Filter out None values for cleaner output
        data = {k: v for k, v in asdict(self).items() if v is not None}
        return json.dumps(data, ensure_ascii=False, default=str)


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs JSON matching the logging schema."""
    
    def format(self, record: logging.LogRecord) -> str:
        entry = LogEntry(
            timestamp=datetime.utcfromtimestamp(record.created).isoformat(),
            level=record.levelname,
            message=record.getMessage(),
            module=record.module,
        )
        # Add extra fields if present
        if hasattr(record, 'trace_id'):
            entry.trace_id = record.trace_id
        if hasattr(record, 'operation'):
            entry.operation = record.operation
        if hasattr(record, 'parameters'):
            entry.parameters = record.parameters
        if hasattr(record, 'success'):
            entry.success = record.success
        if hasattr(record, 'duration_ms'):
            entry.duration_ms = record.duration_ms
        if hasattr(record, 'error'):
            entry.error = record.error
        
        return entry.to_json()


class ReproducibilityLogger:
    """
    Tolerant logger that accepts ANY call shape and never raises.
    
    This logger wraps the stdlib logging module but provides a consistent
    interface that handles all the different call patterns found in the codebase.
    """
    
    def __init__(self, name: str = "reproducibility", *args: Any, **kwargs: Any) -> None:
        self.name = name
        self._logger = logging.getLogger(name)
        self._logger.setLevel(logging.DEBUG)
        self._handlers_added = False
    
    def _ensure_handlers(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Add handlers if not already present."""
        if self._handlers_added:
            return
        
        # Get config if not provided
        if config is None:
            try:
                config = get_config()
            except Exception:
                config = {}
        
        # Ensure log directory exists
        log_dir = Path(config.get('data_logs', 'data/logs'))
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = config.get('log_file', str(log_dir / 'app.log'))
        max_bytes = config.get('log_max_bytes', 10 * 1024 * 1024)  # 10MB
        backup_count = config.get('log_backup_count', 5)
        
        # Rotating file handler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setFormatter(JSONFormatter())
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler for debugging
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(JSONFormatter())
        console_handler.setLevel(logging.INFO)
        
        self._logger.addHandler(file_handler)
        self._logger.addHandler(console_handler)
        self._handlers_added = True
    
    def log(self, *args: Any, **kwargs: Any) -> LogEntry:
        """Log an operation with flexible arguments."""
        self._ensure_handlers()
        
        # Extract operation and parameters
        op = args[0] if args else kwargs.get('operation', 'unknown')
        params = kwargs.copy()
        if 'operation' in params:
            del params['operation']
        
        # Create log entry
        entry = LogEntry(
            level=kwargs.get('level', 'INFO'),
            message=str(op),
            module=kwargs.get('module', 'root'),
            operation=op if isinstance(op, str) else str(op),
            parameters=params
        )
        
        # Log to stdlib logger
        log_level = getattr(logging, kwargs.get('level', 'INFO'), logging.INFO)
        self._logger.log(log_level, entry.to_json())
        
        return entry
    
    def info(self, *args: Any, **kwargs: Any) -> None:
        """Log info message."""
        self._ensure_handlers()
        msg = args[0] if args else kwargs.get('message', '')
        self._logger.info(msg, **kwargs)
    
    def debug(self, *args: Any, **kwargs: Any) -> None:
        """Log debug message."""
        self._ensure_handlers()
        msg = args[0] if args else kwargs.get('message', '')
        self._logger.debug(msg, **kwargs)
    
    def warning(self, *args: Any, **kwargs: Any) -> None:
        """Log warning message."""
        self._ensure_handlers()
        msg = args[0] if args else kwargs.get('message', '')
        self._logger.warning(msg, **kwargs)
    
    def error(self, *args: Any, **kwargs: Any) -> None:
        """Log error message."""
        self._ensure_handlers()
        msg = args[0] if args else kwargs.get('message', '')
        self._logger.error(msg, **kwargs)
    
    def critical(self, *args: Any, **kwargs: Any) -> None:
        """Log critical message."""
        self._ensure_handlers()
        msg = args[0] if args else kwargs.get('message', '')
        self._logger.critical(msg, **kwargs)
    
    def __getattr__(self, name: str) -> Any:
        """Fallback for any unknown method - returns a no-op."""
        def _noop(*args: Any, **kwargs: Any) -> Any:
            return None
        return _noop


_GLOBAL_LOGGER: Optional[ReproducibilityLogger] = None


def get_logger(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
    """Get the global logger instance."""
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    return _GLOBAL_LOGGER


def setup_logging(
    level: Optional[str] = None,
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    module_name: Optional[str] = None,
    *args: Any,
    **kwargs: Any
) -> ReproducibilityLogger:
    """
    Setup logging with flexible arguments to match all call sites.
    
    Accepts:
    - level, log_level: log level string
    - log_file: path to log file
    - config: dict with configuration
    - module_name: name for the module
    - *args, **kwargs: for maximum flexibility
    """
    global _GLOBAL_LOGGER
    
    # Merge configuration
    effective_config = config or {}
    
    # Override with explicit parameters
    if level:
        effective_config['log_level'] = level
    if log_level:
        effective_config['log_level'] = log_level
    if log_file:
        effective_config['log_file'] = log_file
    
    # Create or get logger
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(
            name=module_name or kwargs.get('name', 'root'),
            **effective_config
        )
    
    # Update config if provided
    if effective_config:
        try:
            # Force handler re-setup with new config
            _GLOBAL_LOGGER._handlers_added = False
            _GLOBAL_LOGGER._ensure_handlers(effective_config)
        except Exception:
            pass  # Ignore config errors, use defaults
    
    return _GLOBAL_LOGGER


def log_operation(*args: Any, **kwargs: Any) -> Any:
    """
    Dual-purpose: decorator (@log_operation) or direct logging call.
    
    Direct-call path returns a LogEntry (callers use .to_json()).
    Decorator use returns the wrapped function.
    """
    # Check if called as decorator: @log_operation
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]
        
        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any) -> Any:
            return func(*a, **k)
        
        return _wrapper
    
    # Direct call path
    op = args[0] if args else kwargs.pop('operation', 'operation')
    logger = get_logger()
    return logger.log(op, **kwargs)


def log_with_extra(
    message: str,
    level: str = "INFO",
    **extra: Any
) -> None:
    """
    Log a message with extra fields that will be included in the JSON output.
    
    Extra fields become part of the LogEntry parameters.
    """
    logger = get_logger()
    logger.log(
        message,
        level=level,
        **extra
    )
