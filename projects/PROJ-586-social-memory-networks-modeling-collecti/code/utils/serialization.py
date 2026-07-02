"""
Serialization utilities with file locking.
Implements FR-012: File-locking with fcntl and conflict retry logic.
"""
import os
import json
import time
import fcntl
from pathlib import Path
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)

class FileLockManager:
    """Context manager for file locking with retry logic."""
    
    def __init__(self, file_path: Path, max_retries: int = 5, retry_delay: float = 0.5):
        self.file_path = file_path
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.lock_file = file_path.with_suffix(file_path.suffix + '.lock')
        self._lock_fd = None
    
    def __enter__(self):
        for attempt in range(self.max_retries):
            try:
                # Create lock file if it doesn't exist
                self.lock_file.touch(exist_ok=True)
                self._lock_fd = open(self.lock_file, 'w')
                fcntl.flock(self._lock_fd.fileno(), fcntl.LOCK_EX)
                return self
            except (IOError, OSError) as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Lock acquisition failed, retrying in {self.retry_delay}s... ({attempt+1}/{self.max_retries})")
                    time.sleep(self.retry_delay)
                else:
                    raise RuntimeError(f"Failed to acquire lock after {self.max_retries} attempts") from e
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._lock_fd:
            try:
                fcntl.flock(self._lock_fd.fileno(), fcntl.LOCK_UN)
                self._lock_fd.close()
                # Clean up lock file
                if self.lock_file.exists():
                    self.lock_file.unlink()
            except Exception as e:
                logger.warning(f"Error releasing lock: {e}")

def safe_save(data: Any, file_path: Path, ensure_dir: bool = True) -> bool:
    """
    Safely save data to a file with locking.
    
    Args:
        data: Data to save (must be JSON serializable)
        file_path: Target file path
        ensure_dir: Whether to create parent directories
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if ensure_dir:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with FileLockManager(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
        return True
    except Exception as e:
        logger.error(f"Failed to save data to {file_path}: {e}")
        return False

def safe_load(file_path: Path) -> Optional[Any]:
    """
    Safely load data from a file with locking.
    
    Args:
        file_path: Source file path
        
    Returns:
        Loaded data or None if failed
    """
    try:
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return None
        
        with FileLockManager(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load data from {file_path}: {e}")
        return None
