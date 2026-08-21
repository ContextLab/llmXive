"""
Shared utilities for the llmXive research pipeline.
Provides logging, task ID management, hashing, and directory utilities.
"""
import hashlib
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

# Global state for task context
_current_task_id: Optional[str] = None
_logger_instance: Optional[logging.Logger] = None

class TaskIdFilter(logging.Filter):
    """Filter to inject task_id into log records."""
    def filter(self, record):
        if _current_task_id:
            record.task_id = _current_task_id
        else:
            record.task_id = "N/A"
        return True

def set_task_id(task_id: str) -> None:
    """Set the current task ID for logging context."""
    global _current_task_id
    _current_task_id = task_id

def get_task_id() -> Optional[str]:
    """Get the current task ID."""
    return _current_task_id

def get_unique_id() -> str:
    """Generate a unique ID for this run."""
    return str(uuid.uuid4())

def get_timestamp() -> str:
    """Get current timestamp string."""
    return datetime.now().isoformat()

def setup_logging(
    task_id: Optional[str] = None,
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Setup logging configuration.
    
    Accepts flexible arguments to support various call patterns:
    - setup_logging()
    - setup_logging(task_id="T001")
    - setup_logging(task_id=TASK_ID)
    - setup_logging(level=logging.DEBUG)
    
    Args:
        task_id: Optional task ID to include in logs
        level: Logging level (default: INFO)
        log_file: Optional path to log file
        
    Returns:
        Configured logger instance
    """
    global _logger_instance
    
    # If logger already exists and we aren't reconfiguring, return it
    if _logger_instance and not log_file and not task_id:
        return _logger_instance
    
    logger = logging.getLogger("llmXive")
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] [%(task_id)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Add task ID filter
    task_filter = TaskIdFilter()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(task_filter)
    logger.addHandler(console_handler)
    
    # File handler if requested
    if log_file:
        ensure_directory(log_file)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(task_filter)
        logger.addHandler(file_handler)
    
    # Set global context if task_id provided
    if task_id:
        set_task_id(task_id)
    
    _logger_instance = logger
    return logger

def get_logger() -> logging.Logger:
    """Get the global logger instance."""
    global _logger_instance
    if _logger_instance is None:
        # Initialize with defaults if not set up yet
        _logger_instance = setup_logging()
    return _logger_instance

def log_info(msg: str) -> None:
    """Log an info message."""
    get_logger().info(msg)

def log_error(msg: str) -> None:
    """Log an error message."""
    get_logger().error(msg)

def log_warning(msg: str) -> None:
    """Log a warning message."""
    get_logger().warning(msg)

def compute_sha256(file_path: str) -> str:
    """
    Compute SHA256 hash of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Hex digest of the SHA256 hash
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: str, expected_hash: str) -> bool:
    """
    Verify file checksum against expected hash.
    
    Args:
        file_path: Path to the file
        expected_hash: Expected SHA256 hash
        
    Returns:
        True if hash matches, False otherwise
    """
    actual_hash = compute_sha256(file_path)
    return actual_hash == expected_hash

def ensure_directory(file_path: str) -> str:
    """
    Ensure the directory containing the file path exists.
    
    Args:
        file_path: Path to a file (not a directory)
        
    Returns:
        The created/existing directory path
    """
    dir_path = os.path.dirname(file_path)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
    return dir_path

def safe_json_loads(data: str) -> Optional[Dict[str, Any]]:
    """
    Safely parse JSON string.
    
    Args:
        data: JSON string
        
    Returns:
        Parsed dict or None if invalid
    """
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return None

def safe_json_dumps(obj: Any, **kwargs) -> str:
    """
    Safely serialize object to JSON string.
    
    Args:
        obj: Object to serialize
        **kwargs: Additional args for json.dumps
        
    Returns:
        JSON string
    """
    return json.dumps(obj, **kwargs)

# Import sys here to avoid circular imports if needed
import sys