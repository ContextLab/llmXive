import os
import json
import hashlib
import shutil
from pathlib import Path
from typing import Any, Dict, Optional, List

# Constants
CHECKPOINT_DIR = Path("results/checkpoints")
STATE_DIR = Path("state/projects")

def ensure_checkpoint_dir() -> Path:
    """Ensure the checkpoint directory exists."""
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    return CHECKPOINT_DIR

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_checkpoint_path(run_id: str, step_name: str, suffix: str = ".json") -> Path:
    """Generate the full path for a checkpoint file."""
    ensure_checkpoint_dir()
    safe_run_id = run_id.replace("/", "_").replace("\\", "_")
    safe_step = step_name.replace("/", "_").replace("\\", "_")
    return CHECKPOINT_DIR / f"{safe_run_id}_{safe_step}{suffix}"

def save_checkpoint(run_id: str, step_name: str, data: Dict[str, Any]) -> Path:
    """Save state data to a checkpoint file."""
    path = get_checkpoint_path(run_id, step_name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path

def load_checkpoint(run_id: str, step_name: str) -> Optional[Dict[str, Any]]:
    """Load state data from a checkpoint file if it exists."""
    path = get_checkpoint_path(run_id, step_name)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def has_checkpoint(run_id: str, step_name: str) -> bool:
    """Check if a checkpoint exists for the given run and step."""
    return get_checkpoint_path(run_id, step_name).exists()

def delete_checkpoint(run_id: str, step_name: str) -> bool:
    """Delete a checkpoint file if it exists."""
    path = get_checkpoint_path(run_id, step_name)
    if path.exists():
        path.unlink()
        return True
    return False

def list_checkpoints(run_id: Optional[str] = None) -> List[Path]:
    """List all checkpoint files, optionally filtered by run_id."""
    ensure_checkpoint_dir()
    if run_id:
        safe_run_id = run_id.replace("/", "_").replace("\\", "_")
        return list(CHECKPOINT_DIR.glob(f"{safe_run_id}_*.json"))
    return list(CHECKPOINT_DIR.glob("*.json"))

def save_state_snapshot(run_id: str, snapshot: Dict[str, Any]) -> Path:
    """Save a full state snapshot for a project run."""
    ensure_checkpoint_dir()
    path = get_checkpoint_path(run_id, "full_snapshot")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)
    return path

def get_resume_info(run_id: str, step_name: str) -> Optional[Dict[str, Any]]:
    """Retrieve resume information (last known state) for a specific step."""
    return load_checkpoint(run_id, step_name)