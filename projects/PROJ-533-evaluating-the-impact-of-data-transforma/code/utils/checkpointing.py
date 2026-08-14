import os
import json
import hashlib
import shutil
from pathlib import Path
from typing import Any, Dict, Optional, List

def ensure_checkpoint_dir(checkpoint_dir: str) -> None:
    """Ensures the checkpoint directory exists."""
    Path(checkpoint_dir).mkdir(parents=True, exist_ok=True)

def compute_file_hash(filepath: str) -> str:
    """Computes the SHA256 hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()

def get_checkpoint_path(checkpoint_dir: str, filename: str) -> Path:
    """Returns the full path to a checkpoint file."""
    return Path(checkpoint_dir) / filename

def save_checkpoint(data: Any, checkpoint_dir: str, filename: str) -> None:
    """Saves data to a checkpoint file as JSON."""
    filepath = get_checkpoint_path(checkpoint_dir, filename)
    with open(filepath, 'w') as f:
        json.dump(data, f)

def load_checkpoint(checkpoint_dir: str, filename: str) -> Any:
    """Loads data from a checkpoint file."""
    filepath = get_checkpoint_path(checkpoint_dir, filename)
    with open(filepath, 'r') as f:
        return json.load(f)

def has_checkpoint(checkpoint_dir: str, filename: str) -> bool:
    """Checks if a checkpoint file exists."""
    filepath = get_checkpoint_path(checkpoint_dir, filename)
    return filepath.exists()

def delete_checkpoint(checkpoint_dir: str, filename: str) -> None:
    """Deletes a checkpoint file."""
    filepath = get_checkpoint_path(checkpoint_dir, filename)
    if filepath.exists():
        filepath.unlink()

def list_checkpoints(checkpoint_dir: str) -> List[str]:
    """Lists all checkpoint files in a directory."""
    checkpoint_dir = Path(checkpoint_dir)
    return [f.name for f in checkpoint_dir.glob("*.json") if f.is_file()]

def save_state_snapshot(data: Dict, checkpoint_dir: str):
  """Saves a snapshot of the current state."""
  filepath = Path(checkpoint_dir) / "state.json"
  with open(filepath, 'w') as f:
    json.dump(data, f)

def get_resume_info(checkpoint_dir: str) -> Optional[Dict]:
  """Loads resume information from a checkpoint file."""
  filepath = Path(checkpoint_dir) / "state.json"
  if filepath.exists():
    with open(filepath, 'r') as f:
      return json.load(f)
  return None
