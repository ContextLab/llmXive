import hashlib
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

_task_id: Optional[str] = None

class TaskIdFilter(logging.Filter):
    def filter(self, record):
        record.task_id = _task_id or "UNKNOWN"
        return True

def set_task_id(tid: str):
    global _task_id
    _task_id = tid

def get_task_id() -> Optional[str]:
    return _task_id

def get_unique_id() -> str:
    return str(uuid.uuid4())

def get_timestamp() -> str:
    return datetime.now().isoformat()

def setup_logging(*args, task_id: Optional[str] = None, **kwargs) -> logging.Logger:
    """
    Setup logging infrastructure.
    Compatible with all callers:
    - setup_logging()
    - setup_logging(task_id="T007")
    - setup_logging(level=logging.INFO)
    """
    global _task_id
    if task_id is not None:
        _task_id = task_id
    elif args and isinstance(args[0], str):
        _task_id = args[0]

    logger_name = kwargs.get('name', 'pipeline')
    logger = logging.getLogger(logger_name)

    if logger.handlers:
        # Re-apply task_id if it changed
        for handler in logger.handlers:
            for f in handler.filters:
                if isinstance(f, TaskIdFilter):
                    pass # Filter updates record on call
        return logger

    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s [%(task_id)s] [%(levelname)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        ch.setFormatter(formatter)
        ch.addFilter(TaskIdFilter())
        logger.addHandler(ch)

    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    if name:
        return logging.getLogger(name)
    return logging.getLogger('pipeline')

def log_info(logger: logging.Logger, msg: str):
    logger.info(msg)

def log_error(logger: logging.Logger, msg: str):
    logger.error(msg)

def compute_sha256(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: str, expected_hash: str) -> bool:
    actual_hash = compute_sha256(file_path)
    return actual_hash == expected_hash

def ensure_directory(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def safe_json_loads(data: str) -> Any:
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return None

def safe_json_dumps(obj: Any) -> str:
    return json.dumps(obj, indent=2, default=str)
