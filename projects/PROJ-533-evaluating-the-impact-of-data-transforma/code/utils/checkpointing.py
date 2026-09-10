"""
Checkpointing utilities for state saving and loading to enable pipeline resumption.
Implements Constitution Principle V: State must be preserved to allow recovery.
"""
import os
import json
import hashlib
import shutil
from pathlib import Path
from typing import Any, Dict, Optional, List, Tuple

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CHECKPOINT_DIR = PROJECT_ROOT / "results" / "checkpoints"


def ensure_checkpoint_dir() -> Path:
    """Ensure the checkpoint directory exists."""
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    return CHECKPOINT_DIR


def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_checkpoint_path(run_id: str, step_name: str) -> Path:
    """
    Generate the file path for a checkpoint.
    
    Args:
        run_id: Unique identifier for the simulation run.
        step_name: Name of the pipeline step (e.g., 'download', 'filter').
        
    Returns:
        Path to the checkpoint JSON file.
    """
    safe_run_id = run_id.replace("/", "_").replace("\\", "_")
    safe_step = step_name.replace("/", "_").replace("\\", "_")
    filename = f"{safe_run_id}_{safe_step}.json"
    return ensure_checkpoint_dir() / filename


def save_checkpoint(
    run_id: str,
    step_name: str,
    state: Dict[str, Any],
    extra_metadata: Optional[Dict[str, Any]] = None
) -> Path:
    """
    Save the current pipeline state to a checkpoint file.
    
    Args:
        run_id: Unique identifier for the run.
        step_name: Name of the current step.
        state: Dictionary containing the state to save (e.g., processed_ids, progress).
        extra_metadata: Optional additional metadata to store (e.g., timestamps, config).
        
    Returns:
        Path to the saved checkpoint file.
        
    Raises:
        ValueError: If state is not a dictionary.
        IOError: If the file cannot be written.
    """
    if not isinstance(state, dict):
        raise ValueError(f"State must be a dictionary, got {type(state)}")
    
    checkpoint_path = get_checkpoint_path(run_id, step_name)
    
    payload = {
        "run_id": run_id,
        "step_name": step_name,
        "state": state,
        "metadata": extra_metadata or {},
        "saved_at": None  # Will be set by caller if needed, or left for internal logic
    }
    
    # Add internal consistency check
    payload["internal_hash"] = hashlib.sha256(
        json.dumps(state, sort_keys=True).encode("utf-8")
    ).hexdigest()
    
    with open(checkpoint_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)
        
    return checkpoint_path


def load_checkpoint(run_id: str, step_name: str) -> Optional[Dict[str, Any]]:
    """
    Load a checkpoint if it exists.
    
    Args:
        run_id: Unique identifier for the run.
        step_name: Name of the pipeline step.
        
    Returns:
        Dictionary containing the saved state, or None if no checkpoint exists.
        
    Raises:
        ValueError: If the checkpoint file exists but is corrupted or has mismatched hash.
    """
    checkpoint_path = get_checkpoint_path(run_id, step_name)
    
    if not checkpoint_path.exists():
        return None
    
    try:
        with open(checkpoint_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        
        # Verify integrity
        stored_hash = payload.get("internal_hash")
        state = payload.get("state", {})
        computed_hash = hashlib.sha256(
            json.dumps(state, sort_keys=True).encode("utf-8")
        ).hexdigest()
        
        if stored_hash != computed_hash:
            raise ValueError(
                f"Checkpoint integrity check failed for {checkpoint_path}. "
                f"Stored hash: {stored_hash}, Computed: {computed_hash}. "
                "Data may be corrupted."
            )
        
        return payload
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Checkpoint file {checkpoint_path} is corrupted: {e}")


def has_checkpoint(run_id: str, step_name: str) -> bool:
    """
    Check if a checkpoint exists for a given run and step.
    
    Args:
        run_id: Unique identifier for the run.
        step_name: Name of the pipeline step.
        
    Returns:
        True if a valid checkpoint file exists, False otherwise.
    """
    return get_checkpoint_path(run_id, step_name).exists()


def delete_checkpoint(run_id: str, step_name: str) -> bool:
    """
    Delete a specific checkpoint file.
    
    Args:
        run_id: Unique identifier for the run.
        step_name: Name of the pipeline step.
        
    Returns:
        True if the file was deleted, False if it didn't exist.
    """
    checkpoint_path = get_checkpoint_path(run_id, step_name)
    if checkpoint_path.exists():
        checkpoint_path.unlink()
        return True
    return False


def list_checkpoints(run_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all available checkpoints, optionally filtered by run_id.
    
    Args:
        run_id: Optional filter to only show checkpoints for a specific run.
        
    Returns:
        List of dictionaries containing checkpoint metadata (path, run_id, step_name).
    """
    ensure_checkpoint_dir()
    checkpoints = []
    
    for file_path in CHECKPOINT_DIR.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            
            cp_run_id = payload.get("run_id")
            
            if run_id is None or cp_run_id == run_id:
                checkpoints.append({
                    "path": str(file_path),
                    "run_id": cp_run_id,
                    "step_name": payload.get("step_name"),
                    "saved_at": payload.get("metadata", {}).get("saved_at")
                })
        except (json.JSONDecodeError, KeyError):
            # Skip corrupted files
            continue
            
    return sorted(checkpoints, key=lambda x: x.get("run_id", ""))


def save_state_snapshot(
    run_id: str,
    step_name: str,
    state: Dict[str, Any],
    artifact_hashes: Optional[Dict[str, str]] = None
) -> Path:
    """
    Save a comprehensive state snapshot including artifact hashes for verification.
    This is a specialized wrapper for FR-010 compliance.
    
    Args:
        run_id: Unique identifier for the run.
        step_name: Name of the step.
        state: The pipeline state dictionary.
        artifact_hashes: Dictionary mapping artifact names to their SHA-256 hashes.
        
    Returns:
        Path to the saved checkpoint file.
    """
    extra_meta = {
        "artifact_hashes": artifact_hashes or {},
        "snapshot_type": "full"
    }
    return save_checkpoint(run_id, step_name, state, extra_metadata=extra_meta)


def get_resume_info(run_id: str, step_name: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Helper to determine if a pipeline can resume and retrieve the state.
    
    Args:
        run_id: Unique identifier for the run.
        step_name: Name of the step to check.
        
    Returns:
        Tuple of (can_resume, state_dict). 
        If can_resume is False, state_dict is None.
    """
    checkpoint = load_checkpoint(run_id, step_name)
    if checkpoint is None:
        return False, None
    return True, checkpoint.get("state")