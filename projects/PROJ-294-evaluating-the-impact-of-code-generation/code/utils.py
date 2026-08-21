import hashlib
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Optional, Any, Dict, List, Union

# Global state for task context
_current_task_id: Optional[str] = None

class TaskIdFilter(logging.Filter):
    """Filter to inject task_id into log records."""
    def filter(self, record: logging.LogRecord) -> bool:
        record.task_id = _current_task_id or "UNKNOWN"
        return True

def set_task_id(task_id: str) -> None:
    """Set the global task ID for logging context."""
    global _current_task_id
    _current_task_id = task_id

def get_task_id() -> Optional[str]:
    """Get the current global task ID."""
    return _current_task_id

def get_unique_id() -> str:
    """Generate a unique identifier for this run."""
    return str(uuid.uuid4())

def get_timestamp() -> str:
    """Get the current timestamp in ISO format."""
    return datetime.now().isoformat()

def setup_logging(task_id: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Setup logging infrastructure.
    Accepts:
      - setup_logging()
      - setup_logging(task_id="...")
      - setup_logging(level=logging.INFO)
      - setup_logging(task_id=TASK_ID)
    """
    global _current_task_id
    if task_id is not None:
        _current_task_id = task_id

    # Configure root logger if not already configured
    if not logging.root.handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s [%(levelname)s] [%(task_id)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    logger = logging.getLogger(__name__)
    
    # Ensure the filter is added
    if not any(isinstance(f, TaskIdFilter) for f in logger.filters):
        logger.addFilter(TaskIdFilter())
    
    return logger

def get_logger(name: str = __name__) -> logging.Logger:
    """Get a logger instance, ensuring task_id context is available."""
    logger = logging.getLogger(name)
    if not any(isinstance(f, TaskIdFilter) for f in logger.filters):
        logger.addFilter(TaskIdFilter())
    return logger

def log_info(msg: str) -> None:
    """Log an info message."""
    logging.info(msg)

def log_error(msg: str) -> None:
    """Log an error message."""
    logging.error(msg)

def log_warning(msg: str) -> None:
    """Log a warning message."""
    logging.warning(msg)

def compute_sha256(file_path: str) -> str:
    """Compute the SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")

def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """Verify the SHA256 checksum of a file against an expected value."""
    actual_checksum = compute_sha256(file_path)
    return actual_checksum == expected_checksum

def ensure_directory(path: str) -> bool:
    """Ensure a directory exists, creating it if necessary."""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except OSError as e:
        logging.error(f"Failed to create directory {path}: {e}")
        return False

def safe_json_loads(data: str) -> Any:
    """Safely parse JSON string, returning None on error."""
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return None

def safe_json_dumps(obj: Any) -> Optional[str]:
    """Safely serialize object to JSON string, returning None on error."""
    try:
        return json.dumps(obj, indent=2)
    except (TypeError, ValueError):
        return None
