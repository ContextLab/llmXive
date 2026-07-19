"""
State Management Utility for llmXive Pipeline.

Handles loading, hashing, and updating project state files.
"""

import os
import yaml
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

def load_state_file(path: Path) -> Dict[str, Any]:
    """Load a YAML state file."""
    if not path.exists():
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}

def compute_file_hash(path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_project_state(
    state_path: Path,
    artifact_hashes: Dict[str, str],
    updated_at: Optional[str] = None
) -> None:
    """
    Update the project state file with new artifact hashes and timestamp.

    Args:
        state_path: Path to the state YAML file.
        artifact_hashes: Dictionary mapping artifact names to their hashes.
        updated_at: ISO format timestamp. If None, current time is used.
    """
    state = load_state_file(state_path)
    
    # Update artifact hashes
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}
    state["artifact_hashes"].update(artifact_hashes)
    
    # Update timestamp
    state["updated_at"] = updated_at or datetime.now().isoformat()
    
    # Ensure parent directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(state_path, 'w', encoding='utf-8') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
