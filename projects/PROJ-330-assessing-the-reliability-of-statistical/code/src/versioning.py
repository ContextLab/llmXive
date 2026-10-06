"""
Versioning and state management module.
Computes hashes and maintains state.yaml.
"""
import hashlib
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from src.config import ensure_directories, PROJECT_ROOT, STATE_FILE

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_state() -> Dict[str, Any]:
    """Load the current state from state.yaml."""
    if not STATE_FILE.exists():
        return {"artifacts": {}}
    with open(STATE_FILE, "r") as f:
        return yaml.safe_load(f) or {"artifacts": {}}

def save_state(state: Dict[str, Any]) -> None:
    """Save the state to state.yaml."""
    ensure_directories()
    with open(STATE_FILE, "w") as f:
        yaml.dump(state, f, default_flow_style=False)

def update_artifact_state(name: str, path: Path) -> None:
    """Update the state for a specific artifact."""
    state = load_state()
    if "artifacts" not in state:
        state["artifacts"] = {}
    state["artifacts"][name] = {
        "path": str(path.relative_to(PROJECT_ROOT)),
        "hash": compute_sha256(path),
    }
    save_state(state)

def verify_artifact(name: str, path: Path) -> bool:
    """Verify an artifact's hash against the stored state."""
    state = load_state()
    if name not in state.get("artifacts", {}):
        return False
    stored_hash = state["artifacts"][name].get("hash")
    if not stored_hash:
        return False
    current_hash = compute_sha256(path)
    return current_hash == stored_hash
