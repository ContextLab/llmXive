import hashlib
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Optional

class TaskIdFilter(logging.Filter):
    def __init__(self, task_id: str):
        super().__init__()
        self.task_id = task_id

    def filter(self, record):
        record.task_id = self.task_id
        return True

_task_id: Optional[str] = None
_logger: Optional[logging.Logger] = None

def set_task_id(task_id: str) -> None:
    global _task_id
    _task_id = task_id

def get_task_id() -> Optional[str]:
    return _task_id

def setup_logging(task_id: Optional[str] = None, log_level: int = logging.INFO) -> logging.Logger:
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
    return _logger

def compute_sha256(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    actual_checksum = compute_sha256(file_path)
    return actual_checksum == expected_checksum
