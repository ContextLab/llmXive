"""
Checkpointing utilities for the llmXive pipeline.
Handles saving, loading, and deleting pipeline state with cross-platform
file locking and atomic writes.
"""
import os
import json
import hashlib
import shutil
import tempfile
import platform
from pathlib import Path
from typing import Dict, Optional, Any, List

# Import logger from the existing logging_config module
from code.utils.logging_config import setup_pipeline_logger

logger = setup_pipeline_logger("checkpointing")

CHECKPOINT_DIR = Path("results/checkpoints")

def ensure_checkpoint_dir() -> None:
    """Ensure the checkpoint directory exists."""
    if not CHECKPOINT_DIR.exists():
        CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created checkpoint directory: {CHECKPOINT_DIR}")

def get_checkpoint_path(run_id: str) -> Path:
    """Get the full path for a checkpoint file."""
    ensure_checkpoint_dir()
    return CHECKPOINT_DIR / f"{run_id}.json"

def compute_file_hash(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def _get_lock_file_path(checkpoint_path: Path) -> Path:
    """Get the path for the lock file."""
    return checkpoint_path.with_suffix(checkpoint_path.suffix + ".lock")

def _cross_platform_lock(file_handle, lock_type: str):
    """
    Apply cross-platform file locking.
    lock_type: 'EX' for exclusive lock, 'SH' for shared lock
    """
    if platform.system() == "Windows":
        import msvcrt
        if lock_type == "EX":
            msvcrt.locking(file_handle.fileno(), msvcrt.LK_LOCK, 0)
        else:
            msvcrt.locking(file_handle.fileno(), msvcrt.LK_UNLCK, 0)
    else:
        import fcntl
        if lock_type == "EX":
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX)
        else:
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_SH)

def _cross_platform_unlock(file_handle):
    """Release cross-platform file lock."""
    if platform.system() == "Windows":
        import msvcrt
        msvcrt.locking(file_handle.fileno(), msvcrt.LK_UNLCK, 0)
    else:
        import fcntl
        fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)

def save_state(run_id: str, step: str, data: Dict[str, Any]) -> Path:
    """
    Persist pipeline state to a checkpoint file.

    Args:
        run_id: Unique identifier for the pipeline run.
        step: Current step name/number.
        data: Dictionary containing state data.
             Expected keys: current_dataset_id (str), last_seed (int), error_counts (dict).

    Returns:
        Path to the saved checkpoint file.

    Raises:
        IOError: If file locking or writing fails.
    """
    checkpoint_path = get_checkpoint_path(run_id)
    lock_path = _get_lock_file_path(checkpoint_path)

    # Prepare state content
    state_content = {
        "run_id": run_id,
        "step": step,
        "timestamp": None, # Can be added by caller if needed, or generated here
        "data": data
    }

    # Atomic write with locking
    temp_fd, temp_path = tempfile.mkstemp(
        dir=CHECKPOINT_DIR,
        suffix=".tmp",
        prefix=f"{run_id}_"
    )

    try:
        # Write to temp file
        with os.fdopen(temp_fd, 'w', encoding='utf-8') as temp_file:
            json.dump(state_content, temp_file, indent=2)
            temp_file.flush()
            os.fsync(temp_file.fileno())

        # Lock the target file (if exists) or create lock file
        # We lock the target file path to prevent concurrent writes
        lock_handle = None
        try:
            # Open lock file for locking (create if not exists)
            lock_handle = open(lock_path, 'w')
            _cross_platform_lock(lock_handle, 'EX')

            # Atomic rename
            shutil.move(temp_path, checkpoint_path)
            logger.info(f"Saved checkpoint for run_id={run_id}, step={step}")

        finally:
            if lock_handle:
                _cross_platform_unlock(lock_handle)
                lock_handle.close()
                if lock_path.exists():
                    lock_path.unlink()

        return checkpoint_path

    except Exception as e:
        logger.error(f"Failed to save checkpoint: {e}")
        # Clean up temp file if it exists
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise IOError(f"Checkpoint save failed for run_id={run_id}") from e

def load_state(run_id: str) -> Optional[Dict[str, Any]]:
    """
    Load pipeline state from a checkpoint file.

    Args:
        run_id: Unique identifier for the pipeline run.

    Returns:
        Dictionary containing state data, or None if checkpoint does not exist.
    """
    checkpoint_path = get_checkpoint_path(run_id)
    lock_path = _get_lock_file_path(checkpoint_path)

    if not checkpoint_path.exists():
        logger.debug(f"No checkpoint found for run_id={run_id}")
        return None

    lock_handle = None
    try:
        # Acquire shared lock
        lock_handle = open(lock_path, 'w')
        _cross_platform_lock(lock_handle, 'SH')

        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
            logger.info(f"Loaded checkpoint for run_id={run_id}")
            return content

    except FileNotFoundError:
        logger.warning(f"Checkpoint file disappeared during read for run_id={run_id}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Corrupted checkpoint JSON for run_id={run_id}: {e}")
        return None
    finally:
        if lock_handle:
            _cross_platform_unlock(lock_handle)
            lock_handle.close()
            if lock_path.exists():
                lock_path.unlink()

def delete_checkpoint(run_id: str) -> bool:
    """
    Delete a checkpoint file.

    Args:
        run_id: Unique identifier for the pipeline run.

    Returns:
        True if deleted, False if file did not exist.
    """
    checkpoint_path = get_checkpoint_path(run_id)
    lock_path = _get_lock_file_path(checkpoint_path)

    if not checkpoint_path.exists():
        return False

    lock_handle = None
    try:
        # Exclusive lock before delete
        lock_handle = open(lock_path, 'w')
        _cross_platform_lock(lock_handle, 'EX')

        if checkpoint_path.exists():
            checkpoint_path.unlink()
            logger.info(f"Deleted checkpoint for run_id={run_id}")
            return True

    except Exception as e:
        logger.error(f"Failed to delete checkpoint for run_id={run_id}: {e}")
        return False
    finally:
        if lock_handle:
            _cross_platform_unlock(lock_handle)
            lock_handle.close()
            if lock_path.exists():
                lock_path.unlink()

    return False

def has_checkpoint(run_id: str) -> bool:
    """Check if a checkpoint exists for a given run_id."""
    return get_checkpoint_path(run_id).exists()

def list_checkpoints() -> List[str]:
    """List all available run_ids that have checkpoints."""
    ensure_checkpoint_dir()
    return [f.stem for f in CHECKPOINT_DIR.glob("*.json")]

# Aliases for backward compatibility or convenience
save_checkpoint = save_state
load_checkpoint = load_state
