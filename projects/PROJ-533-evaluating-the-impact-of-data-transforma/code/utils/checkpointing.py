"""
Checkpointing utilities for the llmXive pipeline.
Handles saving, loading, and deleting pipeline state with file locking and atomic writes.
"""
import os
import json
import hashlib
import shutil
import tempfile
import platform
import portalocker
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure the checkpoint directory exists
CHECKPOINT_DIR = Path("results/checkpoints")
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)


def ensure_checkpoint_dir() -> Path:
    """Ensure the checkpoint directory exists."""
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    return CHECKPOINT_DIR


def get_checkpoint_path(run_id: str) -> Path:
    """Generate the file path for a specific run checkpoint."""
    return CHECKPOINT_DIR / f"{run_id}.json"


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file for integrity verification."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return ""


def save_state(run_id: str, step: str, data: Dict[str, Any]) -> None:
    """
    Persist state to a checkpoint file with file locking and atomic writes.

    Args:
        run_id: Unique identifier for the pipeline run.
        step: Current step name in the pipeline.
        data: Dictionary containing state data. Expected keys:
              - current_dataset_id (str)
              - last_seed (int)
              - error_counts (dict)
    """
    ensure_checkpoint_dir()
    checkpoint_path = get_checkpoint_path(run_id)
    temp_path = checkpoint_path.with_suffix('.tmp')

    state = {
        "run_id": run_id,
        "step": step,
        "current_dataset_id": data.get("current_dataset_id", ""),
        "last_seed": data.get("last_seed", 0),
        "error_counts": data.get("error_counts", {}),
        "timestamp": None  # Will be set by caller if needed, or omitted
    }

    try:
        # Write to temp file first
        with open(temp_path, 'w', encoding='utf-8') as f:
            # Lock the file during write
            portalocker.lock(f, portalocker.LOCK_EX)
            try:
                json.dump(state, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            finally:
                portalocker.unlock(f)

        # Atomic rename
        os.replace(temp_path, checkpoint_path)
    except Exception as e:
        # Clean up temp file if it exists
        if temp_path.exists():
            temp_path.unlink()
        raise e


def load_state(run_id: str) -> Optional[Dict[str, Any]]:
    """
    Load state from a checkpoint file with file locking.

    Args:
        run_id: Unique identifier for the pipeline run.

    Returns:
        Dictionary containing state data, or None if checkpoint doesn't exist.
    """
    checkpoint_path = get_checkpoint_path(run_id)
    
    if not checkpoint_path.exists():
        return None

    try:
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            # Lock the file during read
            portalocker.lock(f, portalocker.LOCK_SH)
            try:
                state = json.load(f)
                return state
            finally:
                portalocker.unlock(f)
    except (json.JSONDecodeError, FileNotFoundError, IOError) as e:
        # Return None on read errors
        return None


def delete_checkpoint(run_id: str) -> bool:
    """
    Delete a checkpoint file if it exists.

    Args:
        run_id: Unique identifier for the pipeline run.

    Returns:
        True if checkpoint was deleted, False if it didn't exist.
    """
    checkpoint_path = get_checkpoint_path(run_id)
    
    if checkpoint_path.exists():
        try:
            # Lock before deletion to prevent race conditions
            with open(checkpoint_path, 'a') as f:
                portalocker.lock(f, portalocker.LOCK_EX)
                try:
                    checkpoint_path.unlink()
                    return True
                finally:
                    portalocker.unlock(f)
        except Exception:
            return False
    return False


def has_checkpoint(run_id: str) -> bool:
    """Check if a checkpoint exists for the given run_id."""
    return get_checkpoint_path(run_id).exists()


def list_checkpoints() -> list:
    """List all available checkpoint run_ids."""
    ensure_checkpoint_dir()
    return [
        f.stem 
        for f in CHECKPOINT_DIR.glob("*.json")
        if f.is_file()
    ]