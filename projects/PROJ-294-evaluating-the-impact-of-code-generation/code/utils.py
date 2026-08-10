"""
Shared utilities for the llmXive research pipeline.

Provides logging setup, task ID management, checksums, and safe JSON operations.
"""
import hashlib
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Optional, Any, Dict

# Global state for task ID
_TASK_ID: Optional[str] = None
_LOGGERS: Dict[str, logging.Logger] = {}

class TaskIdFilter(logging.Filter):
    """Logging filter to inject task_id into log records."""
    def filter(self, record):
        record.task_id = get_task_id() or "UNKNOWN"
        return True

def set_task_id(tid: str) -> None:
    """Set the global task ID."""
    global _TASK_ID
    _TASK_ID = tid

def get_task_id() -> Optional[str]:
    """Get the current global task ID."""
    return _TASK_ID

def get_unique_id() -> str:
    """Generate a unique ID string."""
    return str(uuid.uuid4())

def get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now().isoformat()

def setup_logging(task_id: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Set up and return a logger with consistent formatting.

    Accepts various call signatures for flexibility:
    - setup_logging()
    - setup_logging(task_id="T010")
    - setup_logging(task_id=TASK_ID)
    - setup_logging(level=logging.DEBUG)
    - setup_logging("T010")  # Positional task_id

    Args:
        task_id: Optional task ID to inject into logs. Can be string, int (level), or None.
                If an integer is passed, it is treated as the logging level.
        level: Logging level (e.g., logging.INFO, logging.DEBUG).

    Returns:
        Configured logger instance.
    """
    # Handle flexible arguments
    if isinstance(task_id, int):
        # If an integer is passed, treat as level
        level = task_id
        task_id = None
    elif isinstance(task_id, str):
        # If a string is passed, treat as task_id
        pass

    if task_id:
        set_task_id(task_id)

    logger_name = f"llmXive.{get_task_id() or 'root'}"
    logger = logging.getLogger(logger_name)

    # Avoid adding handlers multiple times
    if logger.handlers:
        logger.setLevel(level)
        return logger

    logger.setLevel(level)

    # Create console handler
    handler = logging.StreamHandler()
    handler.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] [%(task_id)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Add filter for task_id
    handler.addFilter(TaskIdFilter())

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Add to registry
    _LOGGERS[logger_name] = logger

    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger by name, creating it if necessary."""
    if name is None:
        name = f"llmXive.{get_task_id() or 'root'}"
    if name not in _LOGGERS:
        return setup_logging()
    return _LOGGERS[name]

def log_info(msg: str) -> None:
    """Log an info message."""
    logger = get_logger()
    logger.info(msg)

def log_error(msg: str) -> None:
    """Log an error message."""
    logger = get_logger()
    logger.error(msg)

def compute_sha256(file_path: str) -> str:
    """
    Compute the SHA256 hash of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal string of the SHA256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """
    Verify a file's checksum against an expected value.

    Args:
        file_path: Path to the file.
        expected_checksum: Expected SHA256 hash.

    Returns:
        True if checksum matches, False otherwise.
    """
    actual_checksum = compute_sha256(file_path)
    return actual_checksum == expected_checksum

def ensure_directory(dir_path: str) -> None:
    """Ensure a directory exists, creating it if necessary."""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)

def safe_json_loads(json_str: str) -> Optional[Any]:
    """
    Safely parse a JSON string.

    Args:
        json_str: JSON string to parse.

    Returns:
        Parsed object or None if parsing fails.
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return None

def safe_json_dumps(obj: Any, indent: int = 2) -> str:
    """
    Safely serialize an object to JSON string.

    Args:
        obj: Object to serialize.
        indent: Indentation level.

    Returns:
        JSON string or empty string if serialization fails.
    """
    try:
        return json.dumps(obj, indent=indent, default=str)
    except (TypeError, ValueError):
        return ""