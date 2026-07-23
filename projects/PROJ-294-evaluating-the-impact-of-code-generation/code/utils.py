"""
Utility functions for the llmXive pipeline.
Provides logging, task ID management, checksums, and directory utilities.
"""
import hashlib
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

# Global task ID storage
_task_id: Optional[str] = None

class TaskIdFilter(logging.Filter):
    """Logging filter to inject Task ID into log records."""
    def filter(self, record):
        record.task_id = get_task_id() or "UNKNOWN"
        return True

def set_task_id(task_id: str):
    """Sets the global task ID."""
    global _task_id
    _task_id = task_id

def get_task_id() -> Optional[str]:
    """Returns the current global task ID."""
    return _task_id

def get_unique_id() -> str:
    """Generates a unique ID for artifacts."""
    return str(uuid.uuid4())

def get_timestamp() -> str:
    """Returns current timestamp in ISO format."""
    return datetime.now().isoformat()

def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Sets up the root logger with console and optional file handlers.
    Injects task ID into log records.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Console Handler
    console_handler = logging.StreamHandler()
    console_format = logging.Formatter(
        '%(asctime)s [%(task_id)s] [%(levelname)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    console_handler.addFilter(TaskIdFilter())
    root_logger.addHandler(console_handler)

    if log_file:
        ensure_directory(os.path.dirname(log_file))
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(console_format)
        file_handler.addFilter(TaskIdFilter())
        root_logger.addHandler(file_handler)

    return root_logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Returns a logger instance, ensuring the task ID filter is present."""
    logger = logging.getLogger(name)
    # Ensure the filter is added if not already present (idempotent)
    if not any(isinstance(f, TaskIdFilter) for f in logger.filters):
        logger.addFilter(TaskIdFilter())
    return logger

def compute_sha256(file_path: str) -> str:
    """Computes the SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: str, expected_hash: str) -> bool:
    """Verifies if a file's SHA256 matches the expected hash."""
    actual_hash = compute_sha256(file_path)
    return actual_hash.lower() == expected_hash.lower()

def ensure_directory(dir_path: str):
    """Creates a directory if it does not exist."""
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)

def safe_json_loads(json_str: str) -> Any:
    """Safely parses a JSON string, returning None on failure."""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None

def safe_json_dumps(obj: Any) -> str:
    """Safely serializes an object to JSON, returning empty string on failure."""
    try:
        return json.dumps(obj, default=str)
    except (TypeError, ValueError):
        return ""
