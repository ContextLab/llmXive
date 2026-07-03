"""
State management system for the molecular reactivity project.
Handles updates to project state YAML files and artifact checksums.
"""
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Project identifier derived from the task description
PROJECT_ID = "PROJ-442-predicting-molecular-reactivity-using-ma"
STATE_DIR = Path("state/projects")
STATE_FILE_NAME = f"{PROJECT_ID}.yaml"
STATE_FILE_PATH = STATE_DIR / STATE_FILE_NAME

def _ensure_state_dir() -> None:
    """Ensure the state directory exists."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)

def _load_state() -> Dict[str, Any]:
    """Load the current state file or return a default structure if it doesn't exist."""
    _ensure_state_dir()
    if STATE_FILE_PATH.exists():
        try:
            with open(STATE_FILE_PATH, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data is None:
                    return _default_state()
                return data
        except Exception as e:
            logger.warning(f"Failed to load state file {STATE_FILE_PATH}: {e}. Starting fresh.")
            return _default_state()
    return _default_state()

def _default_state() -> Dict[str, Any]:
    """Return the default structure for a new state file."""
    return {
        "project_id": PROJECT_ID,
        "last_updated": datetime.utcnow().isoformat(),
        "status": "initialized",
        "artifacts": [],
        "stages": {
            "ingestion": {"status": "pending", "started_at": None, "completed_at": None},
            "preprocessing": {"status": "pending", "started_at": None, "completed_at": None},
            "training": {"status": "pending", "started_at": None, "completed_at": None},
            "evaluation": {"status": "pending", "started_at": None, "completed_at": None}
        }
    }

def _compute_file_checksum(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Cannot compute checksum for missing file: {file_path}")
    
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def _update_artifact_list(
    current_artifacts: List[Dict[str, Any]],
    artifact_path: str,
    artifact_type: str,
    metadata: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Update the artifact list, removing duplicates by path and adding the new entry."""
    # Filter out existing entry with the same path
    filtered = [a for a in current_artifacts if a.get("path") != artifact_path]
    
    new_entry = {
        "path": artifact_path,
        "type": artifact_type,
        "checksum": None,  # Will be set by caller if needed
        "created_at": datetime.utcnow().isoformat(),
        "metadata": metadata or {}
    }
    
    # Compute checksum if file exists
    if Path(artifact_path).exists():
        try:
            new_entry["checksum"] = _compute_file_checksum(artifact_path)
        except Exception as e:
            logger.warning(f"Could not compute checksum for {artifact_path}: {e}")
    
    filtered.append(new_entry)
    return filtered

def update_stage_status(
    stage_name: str,
    status: str,
    started_at: Optional[str] = None,
    completed_at: Optional[str] = None
) -> None:
    """
    Update the status of a specific pipeline stage.
    
    Args:
        stage_name: Name of the stage (e.g., 'ingestion', 'training')
        status: Status string (e.g., 'pending', 'running', 'completed', 'failed')
        started_at: ISO timestamp for start time
        completed_at: ISO timestamp for completion time
    """
    state = _load_state()
    
    if stage_name not in state.get("stages", {}):
        logger.warning(f"Stage '{stage_name}' not found in state. Creating new entry.")
        state["stages"][stage_name] = {
            "status": "pending",
            "started_at": None,
            "completed_at": None
        }
    
    state["stages"][stage_name]["status"] = status
    if started_at:
        state["stages"][stage_name]["started_at"] = started_at
    if completed_at:
        state["stages"][stage_name]["completed_at"] = completed_at
    
    state["last_updated"] = datetime.utcnow().isoformat()
    
    # Update overall project status based on stages
    all_completed = all(
        s.get("status") == "completed" 
        for s in state["stages"].values()
    )
    any_running = any(
        s.get("status") == "running" 
        for s in state["stages"].values()
    )
    
    if all_completed:
        state["status"] = "completed"
    elif any_running:
        state["status"] = "running"
    elif state["status"] == "running":
        state["status"] = "pending" # Reset if not running anymore but not done
    
    _save_state(state)
    logger.info(f"Updated state for stage '{stage_name}' to '{status}'")

def register_artifact(
    artifact_path: str,
    artifact_type: str,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Register a new artifact in the state file.
    
    Args:
        artifact_path: Relative path to the artifact file
        artifact_type: Type of artifact (e.g., 'data', 'model', 'report')
        metadata: Optional dictionary of additional metadata
    """
    state = _load_state()
    
    if "artifacts" not in state:
        state["artifacts"] = []
    
    state["artifacts"] = _update_artifact_list(
        state["artifacts"],
        artifact_path,
        artifact_type,
        metadata
    )
    
    state["last_updated"] = datetime.utcnow().isoformat()
    _save_state(state)
    logger.info(f"Registered artifact: {artifact_path} (type: {artifact_type})")

def get_state() -> Dict[str, Any]:
    """Return the current state dictionary."""
    return _load_state()

def _save_state(state: Dict[str, Any]) -> None:
    """Save the state dictionary to the YAML file."""
    _ensure_state_dir()
    with open(STATE_FILE_PATH, "w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def get_artifact_checksum(artifact_path: str) -> Optional[str]:
    """Retrieve the stored checksum for an artifact if it exists."""
    state = _load_state()
    for artifact in state.get("artifacts", []):
        if artifact.get("path") == artifact_path:
            return artifact.get("checksum")
    return None

def verify_artifact_integrity(artifact_path: str) -> bool:
    """
    Verify the integrity of an artifact by comparing its current checksum
    with the stored checksum in the state file.
    
    Returns:
        True if the checksum matches or if no checksum is stored yet.
        False if the checksums do not match.
    """
    state = _load_state()
    stored_checksum = None
    
    for artifact in state.get("artifacts", []):
        if artifact.get("path") == artifact_path:
            stored_checksum = artifact.get("checksum")
            break
    
    if stored_checksum is None:
        logger.info(f"No stored checksum found for {artifact_path}. Assuming integrity.")
        return True
    
    if not Path(artifact_path).exists():
        logger.error(f"Artifact {artifact_path} does not exist for verification.")
        return False
    
    current_checksum = _compute_file_checksum(artifact_path)
    
    if current_checksum != stored_checksum:
        logger.error(f"Checksum mismatch for {artifact_path}. Stored: {stored_checksum}, Current: {current_checksum}")
        return False
    
    logger.info(f"Artifact {artifact_path} integrity verified.")
    return True
