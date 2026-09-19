import os
import json
import hashlib
import shutil
import fcntl
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure the checkpoint directory exists
CHECKPOINT_DIR = Path("results/checkpoints")

def ensure_checkpoint_dir() -> Path:
    """Creates the checkpoint directory if it doesn't exist."""
    if not CHECKPOINT_DIR.exists():
        CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    return CHECKPOINT_DIR

def get_checkpoint_path(run_id: str) -> Path:
    """Generates the file path for a specific run ID."""
    ensure_checkpoint_dir()
    return CHECKPOINT_DIR / f"{run_id}.json"

def compute_file_hash(file_path: Path) -> Optional[str]:
    """Computes SHA-256 hash of a file for integrity checks."""
    if not file_path.exists():
        return None
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except (IOError, OSError):
        return None

def save_state(run_id: str, step: str, data: Dict[str, Any]) -> bool:
    """
    Persist state to a JSON file with file locking and atomic writes.
    
    Args:
        run_id: Unique identifier for the run.
        step: Current step name or number.
        data: Dictionary containing state data (e.g., current_dataset_id, last_seed, error_counts).
    
    Returns:
        True if successful, False otherwise.
    """
    checkpoint_path = get_checkpoint_path(run_id)
    temp_path = checkpoint_path.with_suffix(".tmp")
    
    state = {
        "run_id": run_id,
        "step": step,
        "data": data,
        "timestamp": None  # Optional, can be added if needed
    }
    
    try:
        # Write to temporary file first
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
            f.flush()
            # Apply file lock while writing
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        
        # Atomic move
        shutil.move(str(temp_path), str(checkpoint_path))
        return True
    except Exception as e:
        # Clean up temp file if it exists
        if temp_path.exists():
            temp_path.unlink()
        return False

def load_state(run_id: str) -> Optional[Dict[str, Any]]:
    """
    Load state from a JSON file for a specific run ID.
    
    Args:
        run_id: Unique identifier for the run.
    
    Returns:
        Dictionary containing state data, or None if not found.
    """
    checkpoint_path = get_checkpoint_path(run_id)
    
    if not checkpoint_path.exists():
        return None
    
    try:
        with open(checkpoint_path, "r", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)
            content = json.load(f)
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            return content.get("data")
    except (IOError, OSError, json.JSONDecodeError):
        return None

def delete_checkpoint(run_id: str) -> bool:
    """
    Delete the checkpoint file for a specific run ID.
    
    Args:
        run_id: Unique identifier for the run.
    
    Returns:
        True if deleted successfully, False otherwise.
    """
    checkpoint_path = get_checkpoint_path(run_id)
    
    if not checkpoint_path.exists():
        return False
    
    try:
        checkpoint_path.unlink()
        return True
    except (IOError, OSError):
        return False

def has_checkpoint(run_id: str) -> bool:
    """
    Check if a checkpoint exists for a specific run ID.
    
    Args:
        run_id: Unique identifier for the run.
    
    Returns:
        True if checkpoint exists, False otherwise.
    """
    return get_checkpoint_path(run_id).exists()

def list_checkpoints() -> list:
    """
    List all available checkpoints in the checkpoint directory.
    
    Returns:
        List of run_ids (strings) for existing checkpoints.
    """
    ensure_checkpoint_dir()
    checkpoints = []
    for file in CHECKPOINT_DIR.glob("*.json"):
        if file.suffix == ".json":
            checkpoints.append(file.stem)
    return sorted(checkpoints)

def save_checkpoint(run_id: str, step: str, data: Dict[str, Any]) -> bool:
    """
    Alias for save_state to provide a more generic interface.
    
    Args:
        run_id: Unique identifier for the run.
        step: Current step name or number.
        data: Dictionary containing state data.
    
    Returns:
        True if successful, False otherwise.
    """
    return save_state(run_id, step, data)

def load_checkpoint(run_id: str) -> Optional[Dict[str, Any]]:
    """
    Alias for load_state to provide a more generic interface.
    
    Args:
        run_id: Unique identifier for the run.
    
    Returns:
        Dictionary containing state data, or None if not found.
    """
    return load_state(run_id)