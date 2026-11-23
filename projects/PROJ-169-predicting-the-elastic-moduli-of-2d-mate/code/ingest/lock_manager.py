"""Lock manager for enforcing single-source data ingestion.

This module handles the lifecycle of the lock file at `data/.source_state`.
It ensures that only one data source is active at a time and prevents
permanent blocks by cleaning up expired locks.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Optional

from filelock import FileLock

# Project root relative to this file
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _PROJECT_ROOT / "data"
_LOCK_FILE_PATH = _DATA_DIR / ".source_state.lock"
_STATE_FILE_PATH = _DATA_DIR / ".source_state"

# Default lock timeout in seconds (1 hour)
DEFAULT_LOCK_TIMEOUT = 3600
# Default expiration threshold for stale locks (2 hours)
DEFAULT_EXPIRATION_THRESHOLD = 7200


def _ensure_data_dir() -> Path:
    """Ensure the data directory exists."""
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    return _DATA_DIR


def acquire_lock(source_name: str, timeout: Optional[float] = None) -> bool:
    """Acquire a lock for the specified data source.

    Args:
        source_name: The identifier of the data source (e.g., 'materials_project').
        timeout: Maximum time to wait for the lock in seconds. Defaults to DEFAULT_LOCK_TIMEOUT.

    Returns:
        True if the lock was acquired successfully, False otherwise.

    Raises:
        RuntimeError: If a lock is already held by a different source.
    """
    _ensure_data_dir()
    lock_path = str(_LOCK_FILE_PATH)
    state_path = str(_STATE_FILE_PATH)

    lock = FileLock(lock_path)

    try:
        # Attempt to acquire the lock
        with lock.acquire(timeout=timeout or DEFAULT_LOCK_TIMEOUT):
            # Check current state
            if _STATE_FILE_PATH.exists():
                try:
                    with open(state_path, "r", encoding="utf-8") as f:
                        state = json.load(f)
                    active_source = state.get("active_source")
                    if active_source and active_source != source_name:
                        raise RuntimeError(
                            f"Lock held by different source: '{active_source}'. "
                            "Switching sources is only allowed between runs, not within a run."
                        )
                except (json.JSONDecodeError, KeyError) as e:
                    # Corrupt state file, treat as no active source but log warning
                    import logging
                    logging.warning(f"Corrupt state file, treating as no active source: {e}")

            # Write new state
            state = {"active_source": source_name, "acquired_at": time.time()}
            with open(state_path, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
            return True

    except Exception as e:
        if "timeout" in str(e).lower():
            return False
        raise


def release_lock(source_name: str) -> bool:
    """Release the lock for the specified data source.

    Args:
        source_name: The identifier of the data source.

    Returns:
        True if the lock was released, False if no lock was held.
    """
    _ensure_data_dir()
    lock_path = str(_LOCK_FILE_PATH)
    state_path = str(_STATE_FILE_PATH)

    lock = FileLock(lock_path)

    try:
        with lock.acquire(timeout=1):
            if not _STATE_FILE_PATH.exists():
                return False

            try:
                with open(state_path, "r", encoding="utf-8") as f:
                    state = json.load(f)
                active_source = state.get("active_source")

                if active_source == source_name:
                    # Remove the state file
                    os.remove(state_path)
                    return True
                else:
                    # Lock held by different source, do not release
                    return False
            except (json.JSONDecodeError, KeyError):
                # Corrupt state, attempt to clean up
                if _STATE_FILE_PATH.exists():
                    os.remove(state_path)
                return False
    except Exception:
        return False


def cleanup_expired_locks(threshold: Optional[float] = None) -> int:
    """Clean up lock files older than the specified threshold.

    This prevents permanent blocks if a process crashes without releasing the lock.

    Args:
        threshold: Time in seconds after which a lock is considered expired.
                   Defaults to DEFAULT_EXPIRATION_THRESHOLD.

    Returns:
        The number of locks cleaned up.
    """
    _ensure_data_dir()
    lock_path = str(_LOCK_FILE_PATH)
    state_path = str(_STATE_FILE_PATH)
    threshold = threshold or DEFAULT_EXPIRATION_THRESHOLD
    current_time = time.time()
    cleaned_count = 0

    lock = FileLock(lock_path)

    try:
        with lock.acquire(timeout=1):
            if _STATE_FILE_PATH.exists():
                try:
                    with open(state_path, "r", encoding="utf-8") as f:
                        state = json.load(f)
                    acquired_at = state.get("acquired_at")

                    if acquired_at is not None:
                        age = current_time - acquired_at
                        if age > threshold:
                            os.remove(state_path)
                            cleaned_count += 1
                            import logging
                            logging.info(f"Cleaned up expired lock (age: {age:.2f}s)")
                except (json.JSONDecodeError, KeyError):
                    # Corrupt state file, remove it
                    os.remove(state_path)
                    cleaned_count += 1
                    import logging
                    logging.warning("Cleaned up corrupt state file")
    except Exception as e:
        import logging
        logging.error(f"Error during lock cleanup: {e}")

    return cleaned_count


def get_active_source() -> Optional[str]:
    """Get the currently active source if a lock is held.

    Returns:
        The source name if a lock is held, None otherwise.
    """
    if not _STATE_FILE_PATH.exists():
        return None

    try:
        with open(_STATE_FILE_PATH, "r", encoding="utf-8") as f:
            state = json.load(f)
        return state.get("active_source")
    except (json.JSONDecodeError, KeyError, IOError):
        return None