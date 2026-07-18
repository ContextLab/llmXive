"""
State Manager Module
Handles atomic updates to the project state YAML file, including SHA256 checksums.
"""
import os
import json
import hashlib
import yaml
from typing import Dict, Any, Optional
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_FILE_PATH = os.path.join(PROJECT_ROOT, 'state', 'projects', 'PROJ-486-investigating-the-impact-of-network-topo.yaml')

def ensure_state_directory():
    """Ensure the state directory exists."""
    state_dir = os.path.dirname(STATE_FILE_PATH)
    if not os.path.exists(state_dir):
        os.makedirs(state_dir, exist_ok=True)

def compute_sha256(file_path: str) -> str:
    """Compute SHA256 hash of a file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found for hashing: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_state() -> Dict[str, Any]:
    """Load the current state YAML file or return a default structure."""
    ensure_state_directory()
    if os.path.exists(STATE_FILE_PATH):
        with open(STATE_FILE_PATH, 'r') as f:
            return yaml.safe_load(f) or {}
    return {
        "project_id": "PROJ-486-investigating-the-impact-of-network-topo",
        "last_updated": None,
        "artifacts": {},
        "pipeline_status": "initialized",
        "data_checksums": {}
    }

def update_state(
    pipeline_status: str,
    artifact_paths: Optional[list] = None,
    data_files: Optional[list] = None
) -> Dict[str, Any]:
    """
    Atomically update the project state.
    
    Args:
        pipeline_status: Current status string (e.g., "completed", "failed")
        artifact_paths: List of relative paths to generated artifacts
        data_files: List of relative paths to data files to checksum
    
    Returns:
        The updated state dictionary
    """
    state = load_state()
    
    # Update timestamp
    state["last_updated"] = datetime.now().isoformat()
    state["pipeline_status"] = pipeline_status
    
    # Update artifact list
    if artifact_paths:
        if "artifacts" not in state:
            state["artifacts"] = {}
        for path in artifact_paths:
            state["artifacts"][path] = {
                "generated_at": state["last_updated"],
                "status": "generated"
            }
    
    # Compute and update checksums for data files
    if data_files:
        if "data_checksums" not in state:
            state["data_checksums"] = {}
        for path in data_files:
            full_path = os.path.join(PROJECT_ROOT, path)
            if os.path.exists(full_path):
                try:
                    checksum = compute_sha256(full_path)
                    state["data_checksums"][path] = {
                        "sha256": checksum,
                        "last_verified": state["last_updated"]
                    }
                except Exception as e:
                    state["data_checksums"][path] = {
                        "error": str(e),
                        "last_verified": state["last_updated"]
                    }
    
    # Write atomically (write to temp, then rename)
    ensure_state_directory()
    temp_path = STATE_FILE_PATH + ".tmp"
    with open(temp_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
    
    os.replace(temp_path, STATE_FILE_PATH)
    
    return state

def get_state() -> Dict[str, Any]:
    """Get the current state without modifying it."""
    return load_state()
