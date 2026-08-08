"""
File-based locking utilities for orchestrating heavy computations.

This module provides a thread-safe, file-system based lock mechanism
to serialize tasks like permutation tests (T025b, T032b) that cannot
run concurrently due to CPU/RAM constraints.
"""
import os
import time
import logging
import fcntl
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

# Configure logger
logger = logging.getLogger(__name__)

# Lock file path as defined in task T045a
LOCK_FILE_PATH = Path("data/interim/pipeline.lock")

# Default timeout for acquiring lock (30 seconds)
DEFAULT_TIMEOUT = 30.0

class PipelineLockError(Exception):
    """Raised when lock acquisition fails or times out."""
    pass


def acquire_lock(lock_path: Optional[Path] = None, timeout: float = DEFAULT_TIMEOUT) -> bool:
    """
    Acquire an exclusive file lock.
    
    Args:
        lock_path: Path to the lock file. Defaults to LOCK_FILE_PATH.
        timeout: Maximum time in seconds to wait for the lock.
        
    Returns:
        True if lock acquired successfully.
        
    Raises:
        PipelineLockError: If lock acquisition times out or fails.
    """
    if lock_path is None:
        lock_path = LOCK_FILE_PATH
    
    # Ensure directory exists
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    
    lock_file = open(lock_path, 'w')
    start_time = time.time()
    
    while True:
        try:
            # Attempt non-blocking lock
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            logger.info(f"Lock acquired: {lock_path}")
            return True
        except (IOError, OSError):
            # Lock is held by another process
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                lock_file.close()
                raise PipelineLockError(
                    f"Failed to acquire lock at {lock_path} after {timeout} seconds. "
                    "Another heavy task (e.g., permutation test) may be running."
                )
            time.sleep(0.5)  # Wait before retrying


def release_lock(lock_path: Optional[Path] = None) -> None:
    """
    Release the file lock.
    
    Args:
        lock_path: Path to the lock file. Defaults to LOCK_FILE_PATH.
    """
    if lock_path is None:
        lock_path = LOCK_FILE_PATH
        
    if lock_path.exists():
        try:
            # We need the file handle to release, but since we don't store it globally,
            # we rely on the process closing the file or using a context manager.
            # However, for robustness, we attempt to open and release.
            with open(lock_path, 'r') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            logger.info(f"Lock released: {lock_path}")
        except (IOError, OSError) as e:
            logger.warning(f"Could not release lock explicitly: {e}")
    else:
        logger.warning(f"Lock file does not exist, nothing to release: {lock_path}")


@contextmanager
def managed_lock(lock_path: Optional[Path] = None, timeout: float = DEFAULT_TIMEOUT):
    """
    Context manager for acquiring and releasing a lock.
    
    Usage:
        with managed_lock():
            # critical section
            pass
            
    Args:
        lock_path: Path to the lock file.
        timeout: Timeout in seconds.
        
    Yields:
        None
        
    Raises:
        PipelineLockError: If lock cannot be acquired.
    """
    lock_file = None
    try:
        if lock_path is None:
            lock_path = LOCK_FILE_PATH
        
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_file = open(lock_path, 'w')
        start_time = time.time()
        
        while True:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                logger.info(f"Lock acquired: {lock_path}")
                break
            except (IOError, OSError):
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    raise PipelineLockError(
                        f"Timeout acquiring lock at {lock_path} after {timeout}s."
                    )
                time.sleep(0.5)
        
        yield
        
    finally:
        if lock_file:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                logger.info(f"Lock released: {lock_path}")
            except Exception as e:
                logger.error(f"Error releasing lock: {e}")
            finally:
                lock_file.close()


def check_lock_status(lock_path: Optional[Path] = None) -> bool:
    """
    Check if the lock is currently held.
    
    Args:
        lock_path: Path to the lock file.
        
    Returns:
        True if locked, False otherwise.
    """
    if lock_path is None:
        lock_path = LOCK_FILE_PATH
        
    if not lock_path.exists():
        return False
        
    try:
        with open(lock_path, 'r') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            return False  # Lock was not held
    except (IOError, OSError):
        return True  # Lock is held


def main():
    """
    CLI entry point for testing the lock mechanism.
    Usage: python -m src.models.lock_utils --acquire --timeout 10
    """
    import argparse
    parser = argparse.ArgumentParser(description="Pipeline Lock Utility")
    parser.add_argument("--acquire", action="store_true", help="Acquire lock and exit")
    parser.add_argument("--release", action="store_true", help="Release lock and exit")
    parser.add_argument("--check", action="store_true", help="Check lock status")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="Timeout in seconds")
    
    args = parser.parse_args()
    
    if args.acquire:
        try:
            acquire_lock(timeout=args.timeout)
            print("Lock acquired successfully.")
        except PipelineLockError as e:
            print(f"Lock acquisition failed: {e}")
            exit(1)
    elif args.release:
        release_lock()
        print("Lock released.")
    elif args.check:
        is_locked = check_lock_status()
        print(f"Lock status: {'LOCKED' if is_locked else 'UNLOCKED'}")
    else:
        parser.print_help()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
