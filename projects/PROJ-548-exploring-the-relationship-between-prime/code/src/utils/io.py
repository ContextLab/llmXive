import hashlib
import os
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import yaml
import time
from datetime import datetime, timezone

# Configuration paths relative to project root
STATE_FILE_PATH = Path("state/projects/PROJ-548-exploring-the-relationship-between-prime.yaml")

def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}

def _save_yaml(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

def load_state() -> Dict[str, Any]:
    """Load the project state file."""
    return _load_yaml(STATE_FILE_PATH)

def save_state(data: Dict[str, Any]) -> None:
    """Save the project state file."""
    _save_yaml(STATE_FILE_PATH, data)

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def compute_directory_checksum(dir_path: Path) -> str:
    """Compute a deterministic checksum for a directory by hashing sorted file checksums."""
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")
    
    files = sorted(dir_path.rglob("*"))
    file_checksums = []
    for file_path in files:
        if file_path.is_file():
            rel_path = file_path.relative_to(dir_path)
            checksum = compute_file_checksum(file_path)
            file_checksums.append(f"{rel_path}:{checksum}")
    
    combined = "\n".join(file_checksums).encode('utf-8')
    return hashlib.sha256(combined).hexdigest()

def update_state_checksums(artifact_path: Path, state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Update the checksum for a specific artifact in the state file.
    Automatically updates the 'updated_at' timestamp (Constitution Principle V).
    """
    if state is None:
        state = load_state()
    
    # Ensure structure exists
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}
    
    # Compute checksum
    checksum = compute_file_checksum(artifact_path)
    
    # Update hash map
    state["artifact_hashes"][str(artifact_path)] = checksum
    
    # Update timestamp (Constitution Principle V)
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Save state
    save_state(state)
    return state

def verify_data_integrity(artifact_path: Path, state: Optional[Dict[str, Any]] = None) -> bool:
    """Verify the checksum of an artifact against the stored state."""
    if state is None:
        state = load_state()
    
    stored_hash = state.get("artifact_hashes", {}).get(str(artifact_path))
    if not stored_hash:
        return False
    
    current_hash = compute_file_checksum(artifact_path)
    return stored_hash == current_hash

def get_data_change_summary(state: Dict[str, Any]) -> str:
    """Generate a human-readable summary of changes in the state."""
    lines = [
        f"State updated at: {state.get('updated_at', 'Unknown')}",
        f"Total artifacts tracked: {len(state.get('artifact_hashes', {}))}"
    ]
    return "\n".join(lines)

def commit_state(artifact_path: Path) -> None:
    """
    Commit an artifact to the state: compute checksum, update hash map,
    and refresh the 'updated_at' timestamp.
    """
    if not artifact_path.exists():
        raise FileNotFoundError(f"Cannot commit non-existent file: {artifact_path}")
    
    state = load_state()
    update_state_checksums(artifact_path, state)

def ensure_state_file_exists() -> None:
    """Ensure the state file exists with minimal structure if not present."""
    if not STATE_FILE_PATH.exists():
        state = {
            "project_id": "PROJ-548-exploring-the-relationship-between-prime",
            "artifact_hashes": {},
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        save_state(state)