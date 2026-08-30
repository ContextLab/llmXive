import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

logger = logging.getLogger(__name__)

def calculate_file_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_project_state(state_path: Path) -> Dict[str, Any]:
    """Load project state from YAML file."""
    if not state_path.exists():
        logger.warning(f"State file not found: {state_path}, returning empty state")
        return {"project_id": "", "artifact_hashes": {}}
    
    with open(state_path, 'r') as f:
        return yaml.safe_load(f) or {"project_id": "", "artifact_hashes": {}}

def save_project_state(state_path: Path, state: Dict[str, Any]) -> None:
    """Save project state to YAML file."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)

def update_artifact_hash(state: Dict[str, Any], artifact_path: str, checksum: str) -> Dict[str, Any]:
    """Update the artifact hash in the project state."""
    state["artifact_hashes"][artifact_path] = checksum
    return state

def verify_artifact_integrity(state: Dict[str, Any], artifact_path: str) -> bool:
    """Verify an artifact's integrity against stored checksum."""
    if artifact_path not in state.get("artifact_hashes", {}):
        logger.warning(f"Artifact {artifact_path} not found in state")
        return False
    
    stored_hash = state["artifact_hashes"][artifact_path]
    file_path = Path(artifact_path)
    
    if not file_path.exists():
        logger.error(f"Artifact file not found: {file_path}")
        return False
    
    current_hash = calculate_file_sha256(file_path)
    
    if current_hash != stored_hash:
        logger.error(f"Checksum mismatch for {artifact_path}")
        logger.error(f"  Expected: {stored_hash}")
        logger.error(f"  Got:      {current_hash}")
        return False
    
    return True

def list_artifacts(state: Dict[str, Any]) -> Dict[str, str]:
    """List all tracked artifacts and their checksums."""
    return state.get("artifact_hashes", {})
