"""
State management module for tracking file checksums and dependencies.
"""
import os
import hashlib
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from config import get_project_root

STATE_FILE = "state.yaml"

def load_state() -> Dict[str, Any]:
    """Load the current state from state.yaml."""
    state_path = get_project_root() / STATE_FILE
    
    if not state_path.exists():
        return {"files": {}, "metadata": {}}
    
    with open(state_path, 'r') as f:
        return yaml.safe_load(f) or {"files": {}, "metadata": {}}

def save_state(state: Dict[str, Any]):
    """Save the state to state.yaml."""
    state_path = get_project_root() / STATE_FILE
    
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def calculate_checksum(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def register_file(file_path: Path, description: str = "", task_id: str = "") -> Dict[str, Any]:
    """Register a file in the state with its checksum and metadata."""
    state = load_state()
    
    if "files" not in state:
        state["files"] = {}
    
    relative_path = str(file_path.relative_to(get_project_root()))
    checksum = calculate_checksum(file_path)
    
    state["files"][relative_path] = {
        "checksum": checksum,
        "timestamp": datetime.now().isoformat(),
        "description": description,
        "task_id": task_id
    }
    
    save_state(state)
    return state["files"][relative_path]

def verify_file(file_path: Path, expected_checksum: Optional[str] = None) -> bool:
    """Verify a file exists and optionally matches an expected checksum."""
    if not file_path.exists():
        return False
    
    if expected_checksum is None:
        return True
    
    actual_checksum = calculate_checksum(file_path)
    return actual_checksum == expected_checksum

def verify_all() -> Dict[str, bool]:
    """Verify all registered files exist and have valid checksums."""
    state = load_state()
    results = {}
    
    for relative_path, info in state.get("files", {}).items():
        file_path = get_project_root() / relative_path
        expected_checksum = info.get("checksum")
        
        if not file_path.exists():
            results[relative_path] = False
            continue
        
        actual_checksum = calculate_checksum(file_path)
        results[relative_path] = actual_checksum == expected_checksum
    
    return results

def get_file_info(file_path: Path) -> Optional[Dict[str, Any]]:
    """Get information about a registered file."""
    state = load_state()
    relative_path = str(file_path.relative_to(get_project_root()))
    
    return state.get("files", {}).get(relative_path)

def clear_stale_entries(threshold_days: int = 30):
    """Remove entries older than threshold_days from the state."""
    state = load_state()
    cutoff = datetime.now().timestamp() - (threshold_days * 86400)
    
    stale_files = []
    for relative_path, info in state.get("files", {}).items():
        try:
            timestamp = datetime.fromisoformat(info["timestamp"]).timestamp()
            if timestamp < cutoff:
                stale_files.append(relative_path)
        except (KeyError, ValueError):
            stale_files.append(relative_path)
    
    for relative_path in stale_files:
        del state["files"][relative_path]
    
    save_state(state)
    return stale_files

def initialize_state():
    """Initialize a new state file."""
    state = {
        "files": {},
        "metadata": {
            "created": datetime.now().isoformat(),
            "version": "1.0"
        }
    }
    save_state(state)
    return state
