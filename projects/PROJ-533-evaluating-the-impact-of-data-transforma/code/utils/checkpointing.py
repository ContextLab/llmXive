import os
import json
import hashlib
import shutil
from pathlib import Path
from typing import Any, Dict, Optional, List

# Define the base checkpoint directory relative to the project root
# This aligns with the project structure created in T001
_CHECKPOINT_DIR = Path("results/checkpoints")

def ensure_checkpoint_dir() -> Path:
    """
    Ensures the checkpoint directory exists. Creates it if necessary.
    
    Returns:
        Path: The absolute path to the checkpoint directory.
    """
    _CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    return _CHECKPOINT_DIR

def compute_file_hash(file_path: Path) -> str:
    """
    Computes the SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        str: Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def get_checkpoint_path(run_id: str, step_name: str = "progress") -> Path:
    """
    Constructs the file path for a specific checkpoint.
    
    Args:
        run_id: Unique identifier for the pipeline run.
        step_name: Name of the specific step or state being saved.
        
    Returns:
        Path: Path to the checkpoint JSON file.
    """
    safe_run_id = run_id.replace("/", "_").replace("\\", "_")
    safe_step_name = step_name.replace("/", "_").replace("\\", "_")
    filename = f"{safe_run_id}_{safe_step_name}.json"
    return _CHECKPOINT_DIR / filename

def save_checkpoint(run_id: str, state: Dict[str, Any], step_name: str = "progress") -> None:
    """
    Saves the current pipeline state to a JSON file.
    
    Args:
        run_id: Unique identifier for the pipeline run.
        state: Dictionary containing the state to save.
        step_name: Name of the step being checkpointed.
    """
    ensure_checkpoint_dir()
    path = get_checkpoint_path(run_id, step_name)
    
    # Add metadata
    state["_metadata"] = {
        "run_id": run_id,
        "step_name": step_name,
        "timestamp": str(Path(path).stat().st_mtime)
    }
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, default=str)

def load_checkpoint(run_id: str, step_name: str = "progress") -> Optional[Dict[str, Any]]:
    """
    Loads a previously saved checkpoint state.
    
    Args:
        run_id: Unique identifier for the pipeline run.
        step_name: Name of the step to load.
        
    Returns:
        Optional[Dict]: The state dictionary if found, None otherwise.
    """
    path = get_checkpoint_path(run_id, step_name)
    if not path.exists():
        return None
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        # Log error in a real system, here we just return None
        return None

def has_checkpoint(run_id: str, step_name: str = "progress") -> bool:
    """
    Checks if a checkpoint exists for the given run and step.
    
    Args:
        run_id: Unique identifier for the pipeline run.
        step_name: Name of the step to check.
        
    Returns:
        bool: True if checkpoint exists, False otherwise.
    """
    return get_checkpoint_path(run_id, step_name).exists()

def delete_checkpoint(run_id: str, step_name: str = "progress") -> bool:
    """
    Deletes a specific checkpoint file.
    
    Args:
        run_id: Unique identifier for the pipeline run.
        step_name: Name of the step to delete.
        
    Returns:
        bool: True if deleted, False if not found.
    """
    path = get_checkpoint_path(run_id, step_name)
    if path.exists():
        path.unlink()
        return True
    return False

def list_checkpoints(run_id: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Lists available checkpoints.
    
    Args:
        run_id: Optional filter to list checkpoints for a specific run.
        
    Returns:
        List[Dict]: List of checkpoint metadata (run_id, step_name, path).
    """
    ensure_checkpoint_dir()
    checkpoints = []
    
    for f in _CHECKPOINT_DIR.glob("*.json"):
        # Parse filename: {run_id}_{step_name}.json
        stem = f.stem
        parts = stem.rsplit("_", 1)
        if len(parts) == 2:
            cid, step = parts
            if run_id is None or cid == run_id:
                checkpoints.append({
                    "run_id": cid,
                    "step_name": step,
                    "path": str(f),
                    "exists": f.exists()
                })
    
    return sorted(checkpoints, key=lambda x: x["path"])

def save_state_snapshot(run_id: str, state: Dict[str, Any]) -> None:
    """
    Saves a full state snapshot for a run (overwriting previous full snapshot).
    This is useful for resuming a full pipeline run from a specific point.
    
    Args:
        run_id: Unique identifier for the pipeline run.
        state: The complete state dictionary to save.
    """
    save_checkpoint(run_id, state, step_name="full_snapshot")

def get_resume_info(run_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves the most recent resume information for a run.
    Looks for a 'full_snapshot' or the most recently modified checkpoint.
    
    Args:
        run_id: Unique identifier for the pipeline run.
        
    Returns:
        Optional[Dict]: The state to resume from, or None if no checkpoint found.
    """
    # First try to load the explicit full snapshot
    snapshot = load_checkpoint(run_id, step_name="full_snapshot")
    if snapshot:
        return snapshot
    
    # Fallback: Find the most recent checkpoint for this run
    checkpoints = list_checkpoints(run_id)
    if not checkpoints:
        return None
    
    # Sort by path (which includes timestamp implicitly in filename if we used time, 
    # but here we rely on file modification time or just pick the last one found)
    # To be robust, we check modification time
    latest = max(checkpoints, key=lambda x: os.path.getmtime(x["path"]))
    
    path = Path(latest["path"])
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None