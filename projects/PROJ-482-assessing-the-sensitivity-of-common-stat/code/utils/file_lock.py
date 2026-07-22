"""
File locking utilities for safe concurrent writes to simulation results.
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
def file_lock(filepath: str, timeout: float = 30.0):
    """
    Context manager for acquiring an exclusive lock on a file.
    
    Args:
        filepath: Path to the file to lock.
        timeout: Maximum time to wait for the lock (seconds).
        
    Yields:
        File object handle.
        
    Raises:
        TimeoutError: If the lock cannot be acquired within timeout.
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Open file in append mode to create if not exists
    fd = os.open(filepath, os.O_CREAT | os.O_RDWR)
    lock_fd = os.fdopen(fd, 'r+')
    
    start_time = time.time()
    acquired = False
    
    try:
        while time.time() - start_time < timeout:
            try:
                fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
                break
            except (IOError, OSError):
                time.sleep(0.1)
        
        if not acquired:
            raise TimeoutError(f"Could not acquire lock on {filepath} within {timeout}s")
        
        yield lock_fd
    finally:
        try:
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
            lock_fd.close()
        except Exception as e:
            logger.warning(f"Error releasing lock on {filepath}: {e}")

def write_pvalue_batch(
    filepath: str,
    records: List[Dict[str, Any]],
    header: Optional[List[str]] = None
):
    """
    Atomically append a batch of p-value records to a CSV file using file locking.
    
    Args:
        filepath: Path to the CSV file.
        records: List of dictionaries representing rows.
        header: Optional list of column names for the header row.
    """
    if not records:
        return

    # Determine if file exists to decide on header writing
    file_exists = os.path.exists(filepath) and os.path.getsize(filepath) > 0
    
    with file_lock(filepath + ".lock"):
        # Use the lock file for exclusive access, but write to the actual file
        # Re-open the actual file for writing inside the lock
        mode = 'w' if not file_exists else 'a'
        
        with open(filepath, mode, newline='') as f:
            writer = csv.DictWriter(f, fieldnames=records[0].keys())
            if not file_exists and header:
                writer.writeheader()
            elif not file_exists:
                # Derive header from first record keys if not provided
                writer.writeheader()
            writer.writerows(records)
        
        logger.info(f"Appended {len(records)} records to {filepath}")
