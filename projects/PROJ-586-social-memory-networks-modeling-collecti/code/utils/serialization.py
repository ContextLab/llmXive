"""
Serialization utilities with file-locking and conflict retry logic.

This module provides thread-safe and process-safe file operations using
fcntl (on Unix-like systems) to prevent race conditions when multiple
processes or threads attempt to write to the same file concurrently.
"""

import fcntl
import time
import os
from pathlib import Path
from typing import Any, Dict, Optional, Callable, TypeVar
import json
import logging

# Import logger from existing utility
from .logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T')

# Configuration constants
DEFAULT_MAX_RETRIES = 5
DEFAULT_RETRY_DELAY = 0.1  # seconds
DEFAULT_BACKOFF_MULTIPLIER = 2.0


class FileLockError(Exception):
    """Raised when file locking fails after all retry attempts."""
    pass


class SerializationError(Exception):
    """Raised when serialization or deserialization fails."""
    pass


def acquire_lock(file_path: Path, timeout: float = 30.0) -> int:
    """
    Acquire an exclusive lock on a file.

    Args:
        file_path: Path to the file to lock
        timeout: Maximum time to wait for lock in seconds

    Returns:
        File descriptor for the locked file

    Raises:
        FileLockError: If lock cannot be acquired within timeout
    """
    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Open file for reading and writing, creating if it doesn't exist
    fd = os.open(str(file_path), os.O_RDWR | os.O_CREAT)

    start_time = time.time()
    attempt = 0

    while True:
        try:
            # Try to acquire exclusive lock (non-blocking)
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            logger.debug(f"Acquired lock on {file_path}")
            return fd
        except (IOError, OSError) as e:
            if e.errno not in (11, 35, 36):  # EAGAIN, EWOULDBLOCK, EACCES
                os.close(fd)
                raise FileLockError(f"Failed to open file {file_path}: {e}")

            # Check timeout
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                os.close(fd)
                raise FileLockError(
                    f"Could not acquire lock on {file_path} within {timeout}s"
                )

            # Exponential backoff
            wait_time = min(DEFAULT_RETRY_DELAY * (DEFAULT_BACKOFF_MULTIPLIER ** attempt), 1.0)
            attempt += 1
            time.sleep(wait_time)


def release_lock(fd: int) -> None:
    """
    Release a file lock.

    Args:
        fd: File descriptor of the locked file
    """
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
        logger.debug("Released file lock")
    except Exception as e:
        logger.warning(f"Error releasing lock: {e}")


def write_with_lock(
    file_path: Path,
    data: Any,
    serializer: Optional[Callable[[Any], str]] = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
    retry_delay: float = DEFAULT_RETRY_DELAY,
    backoff_multiplier: float = DEFAULT_BACKOFF_MULTIPLIER,
    encoding: str = 'utf-8'
) -> bool:
    """
    Write data to a file with exclusive locking and retry logic.

    This function ensures that only one process/thread can write to the file
    at a time, and automatically retries on conflicts.

    Args:
        file_path: Path to the file to write
        data: Data to serialize and write
        serializer: Optional function to convert data to string (default: json.dumps)
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries in seconds
        backoff_multiplier: Multiplier for exponential backoff
        encoding: File encoding

    Returns:
        True if write succeeded, False otherwise

    Raises:
        FileLockError: If lock cannot be acquired after all retries
        SerializationError: If serialization fails
    """
    if serializer is None:
        serializer = lambda d: json.dumps(d, indent=2, default=str)

    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    fd = None
    attempt = 0

    while attempt < max_retries:
        try:
            # Acquire lock
            fd = acquire_lock(file_path, timeout=5.0)

            # Serialize data
            try:
                serialized = serializer(data)
            except Exception as e:
                raise SerializationError(f"Failed to serialize data: {e}")

            # Write to file
            with os.fdopen(fd, 'w', encoding=encoding) as f:
                f.write(serialized)
                f.flush()
                os.fsync(f.fileno())

            logger.debug(f"Successfully wrote {file_path} (attempt {attempt + 1})")
            return True

        except FileLockError as e:
            attempt += 1
            if attempt >= max_retries:
                logger.error(f"Failed to acquire lock on {file_path} after {max_retries} attempts")
                raise
            wait_time = retry_delay * (backoff_multiplier ** attempt)
            logger.warning(f"Lock conflict on {file_path}, retrying in {wait_time:.2f}s (attempt {attempt + 1})")
            time.sleep(wait_time)

        except Exception as e:
            if fd is not None:
                try:
                    release_lock(fd)
                except Exception:
                    pass
            raise SerializationError(f"Failed to write {file_path}: {e}")

    return False


def read_with_lock(
    file_path: Path,
    deserializer: Optional[Callable[[str], Any]] = None,
    encoding: str = 'utf-8'
) -> Any:
    """
    Read data from a file with shared locking.

    Args:
        file_path: Path to the file to read
        deserializer: Optional function to parse string to data (default: json.loads)
        encoding: File encoding

    Returns:
        Deserialized data

    Raises:
        FileNotFoundError: If file does not exist
        SerializationError: If deserialization fails
    """
    if deserializer is None:
        deserializer = json.loads

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    fd = os.open(str(file_path), os.O_RDONLY)
    try:
        # Acquire shared lock
        fcntl.flock(fd, fcntl.LOCK_SH)

        with os.fdopen(fd, 'r', encoding=encoding) as f:
            content = f.read()

        try:
            data = deserializer(content)
            logger.debug(f"Successfully read {file_path}")
            return data
        except Exception as e:
            raise SerializationError(f"Failed to deserialize data from {file_path}: {e}")

    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
        except Exception:
            pass


def atomic_write(
    file_path: Path,
    data: Any,
    serializer: Optional[Callable[[Any], str]] = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
    retry_delay: float = DEFAULT_RETRY_DELAY,
    backoff_multiplier: float = DEFAULT_BACKOFF_MULTIPLIER
) -> bool:
    """
    Atomically write data to a file using a temporary file and rename.

    This ensures that readers never see a partially written file.

    Args:
        file_path: Path to the file to write
        data: Data to serialize and write
        serializer: Optional function to convert data to string
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries in seconds
        backoff_multiplier: Multiplier for exponential backoff

    Returns:
        True if write succeeded, False otherwise
    """
    if serializer is None:
        serializer = lambda d: json.dumps(d, indent=2, default=str)

    file_path = Path(file_path)
    temp_path = file_path.with_suffix(file_path.suffix + '.tmp')

    # Write to temporary file with locking
    if not write_with_lock(
        temp_path,
        data,
        serializer=serializer,
        max_retries=max_retries,
        retry_delay=retry_delay,
        backoff_multiplier=backoff_multiplier
    ):
        return False

    # Atomic rename
    try:
        os.replace(temp_path, file_path)
        logger.debug(f"Atomically replaced {file_path}")
        return True
    except Exception as e:
        # Clean up temp file on failure
        try:
            temp_path.unlink()
        except Exception:
            pass
        logger.error(f"Failed to atomically write {file_path}: {e}")
        return False


class LockedFileWriter:
    """
    Context manager for writing to a file with exclusive locking.

    Usage:
        with LockedFileWriter(Path('output.json')) as writer:
            writer.write(data)
    """

    def __init__(
        self,
        file_path: Path,
        mode: str = 'w',
        encoding: str = 'utf-8'
    ):
        self.file_path = Path(file_path)
        self.mode = mode
        self.encoding = encoding
        self.fd = None
        self.file = None

    def __enter__(self):
        self.fd = acquire_lock(self.file_path, timeout=30.0)
        self.file = os.fdopen(self.fd, self.mode, encoding=self.encoding)
        return self.file

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file is not None:
            self.file.flush()
            self.file.close()
        if self.fd is not None:
            try:
                release_lock(self.fd)
            except Exception:
                pass
        return False


def save_json_with_lock(
    file_path: Path,
    data: Dict[str, Any],
    max_retries: int = DEFAULT_MAX_RETRIES,
    retry_delay: float = DEFAULT_RETRY_DELAY
) -> bool:
    """
    Convenience function to save a dictionary as JSON with file locking.

    Args:
        file_path: Path to output file
        data: Dictionary to save
        max_retries: Maximum retry attempts
        retry_delay: Initial retry delay

    Returns:
        True if save succeeded
    """
    return write_with_lock(
        file_path,
        data,
        serializer=lambda d: json.dumps(d, indent=2, default=str),
        max_retries=max_retries,
        retry_delay=retry_delay
    )


def load_json_with_lock(file_path: Path) -> Dict[str, Any]:
    """
    Convenience function to load a JSON file with file locking.

    Args:
        file_path: Path to input file

    Returns:
        Loaded dictionary
    """
    return read_with_lock(
        file_path,
        deserializer=lambda s: json.loads(s)
    )