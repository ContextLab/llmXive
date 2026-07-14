"""
Logging configuration and utilities for the project.
"""
from __future__ import annotations

import functools
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

import yaml
from pathlib import Path

# Import config
from config import get_config


@dataclass
class LogEntry:
    """Structure for a log entry."""
    timestamp: str
    operation: str
    status: str
    message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


def get_logger(name: str = "project_logger") -> Any:
    """Get a standard python logger."""
    import logging
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def initialize_modeling_log(log_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Initialize the modeling_log.yaml file if it doesn't exist.
    Returns the current log data.
    """
    if log_path is None:
        log_path = get_config("log_path", "modeling_log.yaml")

    path = Path(log_path)
    if not path.exists():
        initial_log = {
            "project": "PROJ-018-adoption-sustainable-agricultural-pra",
            "created_at": datetime.utcnow().isoformat(),
            "sections": {}
        }
        with open(path, 'w') as f:
            yaml.dump(initial_log, f, default_flow_style=False)
        return initial_log

    with open(path, 'r') as f:
        return yaml.safe_load(f) or {}


def update_log_section(section_name: str, updates: Dict[str, Any]) -> None:
    """
    Update a specific section in modeling_log.yaml.
    Handles various call signatures gracefully.
    """
    log_path = get_config("log_path", "modeling_log.yaml")
    path = Path(log_path)

    try:
        if path.exists():
            with open(path, 'r') as f:
                log_data = yaml.safe_load(f) or {}
        else:
            log_data = {"sections": {}}

        if "sections" not in log_data:
            log_data["sections"] = {}

        if section_name not in log_data["sections"]:
            log_data["sections"][section_name] = {}

        # Merge updates
        log_data["sections"][section_name].update(updates)

        # Ensure timestamp is present if not explicitly set
        if "timestamp" not in log_data["sections"][section_name] and "timestamp" not in updates:
            log_data["sections"][section_name]["timestamp"] = datetime.utcnow().isoformat()

        with open(path, 'w') as f:
            yaml.dump(log_data, f, default_flow_style=False)

    except Exception as e:
        # Fail silently to avoid breaking the pipeline on logging errors
        import logging
        logging.getLogger(__name__).error(f"Failed to update log section {section_name}: {e}")


def append_log_entry(operation: str, status: str, message: str = "", details: Dict[str, Any] = None) -> None:
    """Append a new entry to the main log list (if structure supports it)."""
    log_path = get_config("log_path", "modeling_log.yaml")
    path = Path(log_path)

    try:
        if path.exists():
            with open(path, 'r') as f:
                log_data = yaml.safe_load(f) or {}
        else:
            log_data = {"entries": []}

        if "entries" not in log_data:
            log_data["entries"] = []

        entry = LogEntry(
            timestamp=datetime.utcnow().isoformat(),
            operation=operation,
            status=status,
            message=message,
            details=details or {}
        )

        log_data["entries"].append(entry.to_dict())

        with open(path, 'w') as f:
            yaml.dump(log_data, f, default_flow_style=False)

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to append log entry: {e}")


def log_operation(operation_name: str):
    """
    Decorator to log the start and end of an operation.
    Compatible with @log_operation("name") usage.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger()
            logger.info(f"Starting operation: {operation_name}")
            update_log_section(operation_name, {"status": "started", "timestamp": datetime.utcnow().isoformat()})

            try:
                result = func(*args, **kwargs)
                update_log_section(operation_name, {"status": "completed", "timestamp": datetime.utcnow().isoformat()})
                logger.info(f"Completed operation: {operation_name}")
                return result
            except Exception as e:
                update_log_section(operation_name, {"status": "failed", "error": str(e), "timestamp": datetime.utcnow().isoformat()})
                logger.error(f"Failed operation: {operation_name} - {e}")
                raise
        return wrapper
    return decorator
