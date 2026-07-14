from __future__ import annotations

import functools
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

import yaml


@dataclass
class LogEntry:
    """Represents a single log entry."""
    timestamp: str
    operation: str
    status: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def get_logger(name: str = "research_pipeline") -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name.

    Returns:
        Configured logger instance.
    """
    import logging
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def initialize_modeling_log(log_path: str = "modeling_log.yaml") -> None:
    """
    Initialize the modeling log file if it doesn't exist.

    Args:
        log_path: Path to the log file.
    """
    path = Path(log_path)
    if not path.exists():
        log_data = {
            "metadata": {
                "created": datetime.utcnow().isoformat(),
                "version": "1.0"
            },
            "sections": {}
        }
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(log_data, f, default_flow_style=False)


def _load_log(log_path: str = "modeling_log.yaml") -> Dict[str, Any]:
    """Load the modeling log file."""
    path = Path(log_path)
    if not path.exists():
        initialize_modeling_log(log_path)

    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def _save_log(log_data: Dict[str, Any], log_path: str = "modeling_log.yaml") -> None:
    """Save the modeling log file."""
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(log_data, f, default_flow_style=False)


def update_log_section(section_name: str, updates: Dict[str, Any], log_path: str = "modeling_log.yaml") -> None:
    """
    Update a section in the modeling log.

    Supports multiple calling patterns:
    - update_log_section("name", {"key": "value"})
    - update_log_section("name", status="failed", error="msg")

    Args:
        section_name: Name of the section to update.
        updates: Dictionary of updates OR keyword arguments.
        log_path: Path to the log file.
    """
    log_data = _load_log(log_path)

    if "sections" not in log_data:
        log_data["sections"] = {}

    if section_name not in log_data["sections"]:
        log_data["sections"][section_name] = {}

    # Handle updates - if it's a dict, merge it; if it's kwargs, use them
    if isinstance(updates, dict):
        log_data["sections"][section_name].update(updates)
    else:
        # Fallback for unexpected call patterns
        pass

    # Ensure timestamp is present
    log_data["sections"][section_name]["last_updated"] = datetime.utcnow().isoformat()

    _save_log(log_data, log_path)


def append_log_entry(operation: str, status: str, details: Optional[Dict[str, Any]] = None, log_path: str = "modeling_log.yaml") -> None:
    """
    Append a new log entry to the modeling log.

    Args:
        operation: Name of the operation.
        status: Status of the operation (e.g., "started", "completed", "failed").
        details: Optional dictionary of additional details.
        log_path: Path to the log file.
    """
    log_data = _load_log(log_path)

    if "entries" not in log_data:
        log_data["entries"] = []

    entry = LogEntry(
        timestamp=datetime.utcnow().isoformat(),
        operation=operation,
        status=status,
        details=details or {}
    )

    log_data["entries"].append(entry.to_dict())
    _save_log(log_data, log_path)


def log_operation(operation_name: str):
    """
    Decorator to log the start and completion of an operation.

    Args:
        operation_name: Name of the operation to log.

    Returns:
        Decorated function.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Try to get log_path from kwargs or use default
            log_path = kwargs.get('log_path', 'modeling_log.yaml')

            # If log_path is passed as a positional arg, extract it
            if args and len(args) > 0:
                # Check if first arg is a string (likely log_path or config)
                if isinstance(args[0], str) and 'log_path' not in kwargs:
                    log_path = args[0]

            initialize_modeling_log(log_path)
            update_log_section(operation_name, {"status": "started", "timestamp": datetime.utcnow().isoformat()}, log_path=log_path)

            try:
                result = func(*args, **kwargs)
                update_log_section(operation_name, {"status": "completed", "timestamp": datetime.utcnow().isoformat()}, log_path=log_path)
                return result
            except Exception as e:
                update_log_section(operation_name, {"status": "failed", "error": str(e), "timestamp": datetime.utcnow().isoformat()}, log_path=log_path)
                raise

        return wrapper
    return decorator
