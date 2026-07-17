import hashlib
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable

class TaskIdFilter(logging.Filter):
    """
    Logging filter that injects the current task ID into log records.
    Ensures consistent task identification across all log outputs.
    """
    def __init__(self, task_id: str):
        super().__init__()
        self.task_id = task_id

    def filter(self, record: logging.LogRecord) -> bool:
        record.task_id = self.task_id
        return True

_task_id: Optional[str] = None
_logger: Optional[logging.Logger] = None

def set_task_id(task_id: str) -> None:
    """
    Sets the global task ID used for logging context.
    
    Args:
        task_id: The unique identifier for the current task.
    """
    global _task_id
    _task_id = task_id

def get_task_id() -> Optional[str]:
    """
    Retrieves the currently set global task ID.
    
    Returns:
        The task ID string or None if not set.
    """
    return _task_id

def setup_logging(task_id: Optional[str] = None, log_level: int = logging.INFO) -> logging.Logger:
    """
    Configures and returns the project logger with task ID context.
    
    This function initializes a singleton logger instance with a specific
    formatter that includes timestamps, task IDs, and log levels.
    
    Args:
        task_id: Optional task ID to set before logging starts.
        log_level: The logging level (e.g., logging.DEBUG, logging.INFO).
    
    Returns:
        The configured logger instance.
    """
    global _task_id, _logger

    if task_id:
        _task_id = task_id

    if _logger is None:
        logger = logging.getLogger("llmXive")
        logger.setLevel(log_level)

        if not logger.handlers:
            handler = logging.StreamHandler()
            if _task_id:
                handler.addFilter(TaskIdFilter(_task_id))

            formatter = logging.Formatter(
                "%(asctime)s [%(task_id)s] [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        _logger = logger

    return _logger

def get_logger() -> Optional[logging.Logger]:
    """
    Retrieves the initialized logger instance.
    
    Returns:
        The logger instance or None if setup_logging hasn't been called.
    """
    return _logger

def compute_sha256(file_path: str) -> str:
    """
    Computes the SHA256 checksum of a file.
    
    Reads the file in chunks to handle large files efficiently without
    loading the entire content into memory.
    
    Args:
        file_path: Path to the file to hash.
    
    Returns:
        Hexadecimal string representation of the SHA256 hash.
    
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """
    Verifies a file's integrity against an expected SHA256 checksum.
    
    Args:
        file_path: Path to the file to verify.
        expected_checksum: The expected hexadecimal SHA256 checksum.
    
    Returns:
        True if the computed checksum matches the expected one, False otherwise.
    
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    actual_checksum = compute_sha256(file_path)
    return actual_checksum == expected_checksum

def ensure_directory(path: str) -> None:
    """
    Ensures a directory exists, creating it if necessary.
    
    Args:
        path: The directory path to ensure exists.
    """
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def get_unique_id() -> str:
    """
    Generates a unique identifier string.
    
    Returns:
        A UUID4 string.
    """
    return str(uuid.uuid4())

def safe_json_loads(json_string: str) -> Optional[Dict[str, Any]]:
    """
    Safely parses a JSON string, returning None on failure.
    
    Args:
        json_string: The JSON string to parse.
    
    Returns:
        Parsed dictionary or None if parsing fails.
    """
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return None

def safe_json_dumps(data: Any, indent: int = 2) -> str:
    """
    Safely serializes data to a JSON string.
    
    Args:
        data: The data to serialize.
        indent: Indentation level for pretty printing.
    
    Returns:
        JSON string representation or empty string on failure.
    """
    try:
        return json.dumps(data, indent=indent, default=str)
    except (TypeError, ValueError):
        return ""

def get_timestamp() -> str:
    """
    Returns the current timestamp as a formatted string.
    
    Returns:
        ISO format timestamp string.
    """
    return datetime.now().isoformat()