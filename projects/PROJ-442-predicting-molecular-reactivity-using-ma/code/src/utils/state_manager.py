import os
import yaml
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from src.utils.logging import setup_logging

logger = setup_logging(__name__)

PROJECT_ID = "PROJ-442-predicting-molecular-reactivity-using-ma"
STATE_DIR = Path("state/projects")
STATE_FILE_NAME = f"{PROJECT_ID}.yaml"
STATE_FILE_PATH = STATE_DIR / STATE_FILE_NAME

def ensure_state_dir() -> Path:
    """Ensure the state directory exists."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    return STATE_DIR

def compute_checksum(file_path: Path) -> Optional[str]:
    """Compute SHA-256 checksum of a file."""
    if not file_path.exists():
        logger.warning(f"File not found for checksum: {file_path}")
        return None
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error computing checksum for {file_path}: {e}")
        return None

def load_state() -> Dict[str, Any]:
    """Load the current state from the YAML file."""
    if not STATE_FILE_PATH.exists():
        logger.info(f"State file not found. Initializing new state at {STATE_FILE_PATH}")
        return {
            "project_id": PROJECT_ID,
            "last_updated": datetime.utcnow().isoformat(),
            "artifacts": {},
            "pipeline_status": "initialized"
        }
    
    try:
        with open(STATE_FILE_PATH, "r") as f:
            state = yaml.safe_load(f)
            if state is None:
                return {
                    "project_id": PROJECT_ID,
                    "last_updated": datetime.utcnow().isoformat(),
                    "artifacts": {},
                    "pipeline_status": "initialized"
                }
            return state
    except Exception as e:
        logger.error(f"Error loading state file: {e}")
        raise

def save_state(state: Dict[str, Any]) -> None:
    """Save the state to the YAML file."""
    ensure_state_dir()
    state["last_updated"] = datetime.utcnow().isoformat()
    try:
        with open(STATE_FILE_PATH, "w") as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False)
        logger.info(f"State saved to {STATE_FILE_PATH}")
    except Exception as e:
        logger.error(f"Error saving state file: {e}")
        raise

def update_artifact_state(
    artifact_path: Path, 
    artifact_name: Optional[str] = None, 
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Update the state with a new artifact entry.
    
    Args:
        artifact_path: Path to the artifact file.
        artifact_name: Optional name for the artifact. Defaults to filename.
        metadata: Optional additional metadata to store.
    """
    state = load_state()
    
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")
    
    name = artifact_name or artifact_path.name
    checksum = compute_checksum(artifact_path)
    
    if checksum is None:
        raise ValueError(f"Could not compute checksum for {artifact_path}")
    
    artifact_entry = {
        "path": str(artifact_path),
        "checksum": checksum,
        "created_at": datetime.utcnow().isoformat(),
        "type": artifact_path.suffix.lstrip('.') or "unknown"
    }
    
    if metadata:
        artifact_entry["metadata"] = metadata
    
    state["artifacts"][name] = artifact_entry
    
    # Update pipeline status if it was 'initialized'
    if state.get("pipeline_status") == "initialized":
        state["pipeline_status"] = "active"
        
    save_state(state)
    logger.info(f"Updated state with artifact: {name}")

def update_pipeline_status(status: str) -> None:
    """Update the overall pipeline status in the state file."""
    state = load_state()
    state["pipeline_status"] = status
    save_state(state)
    logger.info(f"Pipeline status updated to: {status}")
