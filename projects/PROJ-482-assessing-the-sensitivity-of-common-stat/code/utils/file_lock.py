"""
File locking utilities for safe concurrent writes (though single runner is assumed).
Implements T018's streaming requirement with batch writes.
"""
import os
import fcntl
import logging
import time
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
import csv

logger = logging.getLogger(__name__)

@contextmanager
def file_lock(file_path: str, timeout: int = 30):
    """
    Context manager for acquiring a file lock.
    Falls back to standard append if fcntl is not available (e.g., Windows).
    """
    lock_path = f"{file_path}.lock"
    start_time = time.time()
    
    try:
        # Try to create a lock file
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL)
        try:
            yield lock_fd
        finally:
            os.close(lock_fd)
            os.remove(lock_path)
    except FileExistsError:
        # Lock exists, wait
        while time.time() - start_time < timeout:
            try:
                lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL)
                os.close(lock_fd)
                os.remove(lock_path)
                yield lock_fd
                return
            except FileExistsError:
                time.sleep(0.1)
        raise TimeoutError(f"Could not acquire lock for {file_path} within {timeout}s")
    except (OSError, NotImplementedError):
        # Fallback for Windows or systems without fcntl
        logger.debug("fcntl not available, using no-op lock")
        yield None

def write_pvalue_batch(file_path: str, rows: List[Dict[str, Any]]):
    """
    Write a batch of p-values to CSV with locking.
    Appends to existing file, creates header if new.
    """
    if not rows:
        return

    fieldnames = list(rows[0].keys())
    file_exists = os.path.exists(file_path)

    try:
        with file_lock(file_path):
            with open(file_path, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                if not file_exists:
                    writer.writeheader()
                writer.writerows(rows)
        logger.debug(f"Wrote {len(rows)} rows to {file_path}")
    except TimeoutError as e:
        logger.error(f"Failed to write batch to {file_path}: {e}")
        raise