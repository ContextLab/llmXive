"""
Runtime source enforcement for single canonical data source.

This module ensures that only one data source (Materials Project or AFLOW)
is active per run, satisfying Constitution Principle I.
"""
import os
import sys
import fcntl
import time
from pathlib import Path

STATE_FILE = Path("data/.source_state")
LOCK_FILE = Path("data/.source_state.lock")

def _acquire_lock(lock_path: Path, timeout: float = 10.0) -> bool:
    """Attempt to acquire a file lock with a timeout."""
    if not lock_path.parent.exists():
        lock_path.parent.mkdir(parents=True, exist_ok=True)
    
    start_time = time.time()
    while True:
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR)
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fd
        except (IOError, OSError):
            if time.time() - start_time > timeout:
                return -1
            time.sleep(0.1)

def _release_lock(fd: int, lock_path: Path) -> None:
    """Release a file lock and close the descriptor."""
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
        if lock_path.exists():
            lock_path.unlink()
    except Exception:
        pass

def enforce_single_source(source: str) -> None:
    """
    Enforce that only one data source is active per run.
    
    This function uses a lock file to prevent concurrent access and a state
    file to persist the source identity across runs.
    
    Args:
        source: The requested source ('materials_project' or 'aflow').
    
    Raises:
        SystemExit: If a different source was previously recorded, if multiple
                    sources are detected, or if the source is invalid.
    """
    if not source:
        raise ValueError("Source cannot be empty.")
    
    valid_sources = {'materials_project', 'aflow'}
    if source not in valid_sources:
        error_msg = f"Invalid source '{source}'. Must be one of: {', '.join(valid_sources)}"
        print(f"ERROR: {error_msg}", file=sys.stderr)
        raise SystemExit(1)

    # Ensure data directory exists
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Acquire lock to prevent concurrent/mixed source activation
    lock_fd = _acquire_lock(LOCK_FILE, timeout=10.0)
    if lock_fd == -1:
        print("ERROR: Could not acquire lock on source state file. Another process may be running.", file=sys.stderr)
        raise SystemExit(1)

    try:
        # Check for existing state
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, "r") as f:
                    state_content = f.read().strip()
                # Parse state: expected format "source:timestamp" or just "source"
                state_source = state_content.split(":")[0] if ":" in state_content else state_content
                
                if state_source != source:
                    error_msg = f"Source mismatch: State file indicates {state_source}, but DATA_SOURCE={source}"
                    print(f"ERROR: {error_msg}", file=sys.stderr)
                    raise SystemExit(1)
                
                # Source matches, update timestamp to indicate active run
                with open(STATE_FILE, "w") as f:
                    f.write(f"{source}:{time.time()}")
            except Exception as e:
                print(f"ERROR: Failed to read/write state file: {e}", file=sys.stderr)
                raise SystemExit(1)
        else:
            # Create state file for first run
            with open(STATE_FILE, "w") as f:
                f.write(f"{source}:{time.time()}")
            
            print(f"INFO: Source state initialized to {source}")
    finally:
        _release_lock(lock_fd, LOCK_FILE)

def clear_source_state() -> None:
    """Clear the source state file (for testing/resetting)."""
    if STATE_FILE.exists():
        STATE_FILE.unlink()
    if LOCK_FILE.exists():
        try:
            LOCK_FILE.unlink()
        except Exception:
            pass