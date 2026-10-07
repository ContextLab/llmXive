"""
Checkpointing utilities for the llmXive pipeline.

Provides functions to save, load, and delete pipeline state checkpoints
with file locking and atomic writes to ensure data integrity.
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

# Ensure the results directory exists
RESULTS_DIR = Path("results")
CHECKPOINT_DIR = RESULTS_DIR / "checkpoints"

def ensure_checkpoint_dir():
    """Ensure the checkpoint directory exists."""
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    return CHECKPOINT_DIR

def get_checkpoint_path(run_id: str) -> Path:
    """Get the full path for a checkpoint file."""
    ensure_checkpoint_dir()
    return CHECKPOINT_DIR / f"{run_id}.json"

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file for integrity verification."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_state(run_id: str, step: str, data: Dict[str, Any]) -> None:
    """
    Persist pipeline state to a checkpoint file.
    
    Args:
        run_id: Unique identifier for the run
        step: Current step name/number
        data: Dictionary containing state data. Expected keys include:
             - current_dataset_id (str)
             - last_seed (int)
             - error_counts (dict)
    
    Raises:
        IOError: If file locking or write fails
        ValueError: If data structure is invalid
    """
    # Validate required fields
    if not isinstance(data, dict):
        raise ValueError("data must be a dictionary")
    
    checkpoint_path = get_checkpoint_path(run_id)
    temp_path = checkpoint_path.with_suffix('.tmp')
    
    state = {
        "run_id": run_id,
        "step": step,
        "current_dataset_id": data.get("current_dataset_id", ""),
        "last_seed": data.get("last_seed", 0),
        "error_counts": data.get("error_counts", {}),
        "platform": platform.system(),
        "timestamp": None  # Will be set by caller if needed
    }
    
    try:
        # Write to temporary file first
        with open(temp_path, 'w', encoding='utf-8') as f:
            # Acquire exclusive lock
            portalocker.lock(f, portalocker.LOCK_EX)
            try:
                json.dump(state, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            finally:
                portalocker.unlock(f)
        
        # Atomic rename
        shutil.move(str(temp_path), str(checkpoint_path))
        
    except Exception as e:
        # Clean up temp file if it exists
        if temp_path.exists():
            temp_path.unlink()
        raise IOError(f"Failed to save checkpoint for run {run_id}: {e}") from e

def load_state(run_id: str) -> Optional[Dict[str, Any]]:
    """
    Load pipeline state from a checkpoint file.
    
    Args:
        run_id: Unique identifier for the run
    
    Returns:
        Dictionary containing state data, or None if checkpoint doesn't exist
    
    Raises:
        IOError: If file locking or read fails
        json.JSONDecodeError: If checkpoint file is corrupted
    """
    checkpoint_path = get_checkpoint_path(run_id)
    
    if not checkpoint_path.exists():
        return None
    
    try:
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            # Acquire shared lock for reading
            portalocker.lock(f, portalocker.LOCK_SH)
            try:
                state = json.load(f)
            finally:
                portalocker.unlock(f)
        return state
        
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Corrupted checkpoint file for run {run_id}", e.doc, e.pos
        ) from e
    except Exception as e:
        raise IOError(f"Failed to load checkpoint for run {run_id}: {e}") from e

def delete_checkpoint(run_id: str) -> bool:
    """
    Delete a checkpoint file.
    
    Args:
        run_id: Unique identifier for the run
    
    Returns:
        True if checkpoint was deleted, False if it didn't exist
    
    Raises:
        IOError: If deletion fails
    """
    checkpoint_path = get_checkpoint_path(run_id)
    
    if not checkpoint_path.exists():
        return False
    
    try:
        checkpoint_path.unlink()
        return True
    except Exception as e:
        raise IOError(f"Failed to delete checkpoint for run {run_id}: {e}") from e

def has_checkpoint(run_id: str) -> bool:
    """
    Check if a checkpoint exists for the given run ID.
    
    Args:
        run_id: Unique identifier for the run
    
    Returns:
        True if checkpoint exists, False otherwise
    """
    return get_checkpoint_path(run_id).exists()

def list_checkpoints() -> list:
    """
    List all available checkpoint run IDs.
    
    Returns:
        List of run IDs that have checkpoints
    """
    ensure_checkpoint_dir()
    checkpoints = []
    for file_path in CHECKPOINT_DIR.glob("*.json"):
        checkpoints.append(file_path.stem)
    return sorted(checkpoints)
