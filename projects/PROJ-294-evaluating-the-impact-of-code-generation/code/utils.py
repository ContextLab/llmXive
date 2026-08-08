"""
Utility functions for the llmXive project.

Provides logging, task ID tracking, checksums, and other shared utilities.
"""
import hashlib
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Optional, Any

# Global task ID
_task_id: Optional[str] = None

class TaskIdFilter(logging.Filter):
    """Filter to add task_id to log records."""
    def filter(self, record):
        record.task_id = get_task_id() or "UNKNOWN"
        return True

def set_task_id(tid: Optional[str]):
    """Set the global task ID."""
    global _task_id
    _task_id = tid

def get_task_id() -> Optional[str]:
    """Get the current global task ID."""
    return _task_id

def get_unique_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())

def get_timestamp() -> str:
    """Get current timestamp as string."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def setup_logging(task_id: Optional[str] = None, name: Optional[str] = None) -> logging.Logger:
    """
    Setup logging infrastructure with timestamp and task ID tracking.
    
    This function is designed to be tolerant of various call signatures:
    - setup_logging() -> returns default logger
    - setup_logging(task_id="T001") -> sets task_id and returns logger
    - setup_logging(name="my_module") -> returns named logger
    - setup_logging(task_id="T001", name="my_module") -> sets task_id and returns named logger
    
    Args:
        task_id: Optional task ID to set globally and include in logs
        name: Optional logger name
        
    Returns:
        logging.Logger instance
    """
    global _task_id
    
    # Handle task_id parameter
    if task_id is not None:
        _task_id = task_id
    
    # Create or get logger
    if name:
        logger = logging.getLogger(name)
    else:
        logger = logging.getLogger(__name__)
    
    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter with task_id
        formatter = logging.Formatter(
            '%(asctime)s - %(task_id)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Add task_id filter
        console_handler.addFilter(TaskIdFilter())
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger by name.
    
    Args:
        name: Logger name
        
    Returns:
        logging.Logger instance
    """
    return logging.getLogger(name)

def log_info(logger: logging.Logger, message: str):
    """Log an info message."""
    logger.info(message)

def log_error(logger: logging.Logger, message: str):
    """Log an error message."""
    logger.error(message)

def compute_sha256(file_path: str) -> str:
    """
    Compute SHA256 checksum of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        SHA256 hex digest
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """
    Verify file checksum.
    
    Args:
        file_path: Path to the file
        expected_checksum: Expected SHA256 hex digest
        
    Returns:
        True if checksum matches, False otherwise
    """
    actual_checksum = compute_sha256(file_path)
    return actual_checksum == expected_checksum

def ensure_directory(dir_path: str) -> str:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        dir_path: Path to the directory
        
    Returns:
        The directory path
    """
    os.makedirs(dir_path, exist_ok=True)
    return dir_path

def safe_json_loads(json_string: str) -> Optional[Any]:
    """
    Safely parse JSON string.
    
    Args:
        json_string: JSON string to parse
        
    Returns:
        Parsed object or None if parsing fails
    """
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return None

def safe_json_dumps(obj: Any) -> str:
    """
    Safely serialize object to JSON string.
    
    Args:
        obj: Object to serialize
        
    Returns:
        JSON string or empty string if serialization fails
    """
    try:
        return json.dumps(obj, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return ""
