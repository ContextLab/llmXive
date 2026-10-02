import hashlib
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Optional, Any, Dict

# Global state for task context
_task_id: Optional[str] = None
_unique_id: Optional[str] = None

class TaskIdFilter(logging.Filter):
    """Filter to add task_id to log records."""
    def filter(self, record):
        if _task_id:
            record.task_id = _task_id
        return True

def set_task_id(task_id: str) -> None:
    """Set the global task ID for logging context."""
    global _task_id
    _task_id = task_id

def get_task_id() -> Optional[str]:
    """Get the current task ID."""
    return _task_id

def get_unique_id() -> str:
    """Generate or return a unique ID for the current run."""
    global _unique_id
    if not _unique_id:
        _unique_id = str(uuid.uuid4())
    return _unique_id

def get_timestamp() -> str:
    """Get current timestamp string."""
    return datetime.now().isoformat()

def setup_logging(task_id: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Setup logging infrastructure with task ID and unique run ID.
    
    Accepts flexible arguments to support various call patterns:
    - setup_logging()
    - setup_logging(task_id="T001a")
    - setup_logging(task_id=TASK_ID)
    - setup_logging(level=logging.INFO)
    
    Args:
        task_id: Optional task identifier.
        level: Logging level (default INFO).
        
    Returns:
        logging.Logger: Configured logger instance.
    """
    # Handle flexible argument passing
    if task_id is not None:
        set_task_id(task_id)
    
    # Use a consistent logger name
    logger_name = "llmXive"
    logger = logging.getLogger(logger_name)
    
    # Avoid adding handlers multiple times
    if not logger.handlers:
        logger.setLevel(level)
        
        # Create console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        
        # Create formatter with task_id and timestamp
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] [%(task_id)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        formatter.converter = datetime.fromtimestamp
        
        # Add task_id filter
        task_filter = TaskIdFilter()
        ch.addFilter(task_filter)
        
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    
    # Ensure task_id is in record if not set
    if not _task_id:
        set_task_id("GLOBAL")
        
    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance, optionally with a specific name.
    
    Args:
        name: Optional logger name suffix.
        
    Returns:
        logging.Logger: Logger instance.
    """
    base_name = "llmXive"
    if name:
        base_name = f"{base_name}.{name}"
    return logging.getLogger(base_name)

def log_info(message: str, logger: Optional[logging.Logger] = None) -> None:
    """Log an info message."""
    if logger is None:
        logger = get_logger()
    logger.info(message)

def log_error(message: str, logger: Optional[logging.Logger] = None) -> None:
    """Log an error message."""
    if logger is None:
        logger = get_logger()
    logger.error(message)

def log_warning(message: str, logger: Optional[logging.Logger] = None) -> None:
    """Log a warning message."""
    if logger is None:
        logger = get_logger()
    logger.warning(message)

def compute_sha256(file_path: str) -> str:
    """
    Compute SHA256 hash of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        str: Hex digest of the SHA256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: str, expected_hash: str) -> bool:
    """
    Verify file hash against expected value.
    
    Args:
        file_path: Path to the file.
        expected_hash: Expected SHA256 hex string.
        
    Returns:
        bool: True if hash matches, False otherwise.
    """
    actual_hash = compute_sha256(file_path)
    return actual_hash.lower() == expected_hash.lower().strip()

def ensure_directory(path: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path.
        
    Returns:
        bool: True if directory exists or was created, False on error.
    """
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except OSError:
        return False

def safe_json_loads(json_str: str) -> Any:
    """
    Safely parse JSON string.
    
    Args:
        json_str: JSON string.
        
    Returns:
        Parsed object or None on error.
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return None

def safe_json_dumps(obj: Any, **kwargs) -> str:
    """
    Safely serialize object to JSON string.
    
    Args:
        obj: Object to serialize.
        **kwargs: Additional json.dumps arguments.
        
    Returns:
        JSON string or empty string on error.
    """
    try:
        return json.dumps(obj, **kwargs)
    except (TypeError, ValueError):
        return ""

# Import sys here to avoid circular imports if needed in setup_logging
import sys
