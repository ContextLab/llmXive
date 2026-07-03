import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.logging import setup_logger, get_logger

logger = get_logger(__name__)

PROJECT_ID = "PROJ-442-predicting-molecular-reactivity-using-ma"
STATE_DIR = Path("state/projects")
STATE_FILE = STATE_DIR / f"{PROJECT_ID}.yaml"

def _ensure_state_file() -> Path:
    """Ensure the state file and directory exist, initializing if necessary."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if not STATE_FILE.exists():
        initial_state = {
            "project_id": PROJECT_ID,
            "created_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat(),
            "stages": {},
            "artifacts": []
        }
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(initial_state, f, indent=2)
        logger.info(f"Initialized new state file at {STATE_FILE}")
    return STATE_FILE

def _load_state() -> Dict[str, Any]:
    """Load the current state from the YAML/JSON file."""
    _ensure_state_file()
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_state(state: Dict[str, Any]) -> None:
    """Save the state back to the file."""
    state["last_updated"] = datetime.utcnow().isoformat()
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def get_state() -> Dict[str, Any]:
    """Get the current project state."""
    return _load_state()

def get_artifact_checksum(artifact_path: str) -> Optional[str]:
    """
    Compute the SHA-256 checksum of a file.
    Returns None if the file does not exist.
    """
    path = Path(artifact_path)
    if not path.exists():
        return None
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def register_artifact(artifact_path: str, artifact_type: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    """
    Register a new artifact in the state file.
    If the artifact already exists, it updates the checksum and metadata.
    """
    state = _load_state()
    abs_path = str(Path(artifact_path).resolve())
    checksum = get_artifact_checksum(abs_path)

    if checksum is None:
        logger.warning(f"Artifact not found for registration: {abs_path}")
        return

    existing_entry = None
    for entry in state.get("artifacts", []):
        if entry.get("path") == abs_path:
            existing_entry = entry
            break

    artifact_record = {
        "path": abs_path,
        "type": artifact_type,
        "checksum": checksum,
        "registered_at": datetime.utcnow().isoformat(),
        "metadata": metadata or {}
    }

    if existing_entry:
        logger.info(f"Updating artifact registration: {abs_path}")
        existing_entry.update(artifact_record)
    else:
        logger.info(f"Registering new artifact: {abs_path}")
        state.setdefault("artifacts", []).append(artifact_record)

    _save_state(state)

def verify_artifact_integrity(artifact_path: str) -> bool:
    """
    Verify that an artifact's current checksum matches the one stored in the state.
    Returns True if valid, False if mismatch or missing.
    """
    state = _load_state()
    abs_path = str(Path(artifact_path).resolve())

    current_checksum = get_artifact_checksum(abs_path)
    if current_checksum is None:
        logger.error(f"Artifact missing for integrity check: {abs_path}")
        return False

    for entry in state.get("artifacts", []):
        if entry.get("path") == abs_path:
            stored_checksum = entry.get("checksum")
            if current_checksum == stored_checksum:
                logger.debug(f"Artifact integrity verified: {abs_path}")
                return True
            else:
                logger.error(f"Checksum mismatch for {abs_path}. Expected: {stored_checksum}, Got: {current_checksum}")
                return False

    logger.error(f"Artifact not found in state for integrity check: {abs_path}")
    return False

def update_stage_status(stage_name: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Update the status of a specific stage in the state file.
    Statuses: 'pending', 'running', 'completed', 'failed'
    """
    state = _load_state()
    if "stages" not in state:
        state["stages"] = {}

    stage_record = {
        "status": status,
        "updated_at": datetime.utcnow().isoformat(),
        "details": details or {}
    }

    state["stages"][stage_name] = stage_record
    _save_state(state)
    logger.info(f"Updated stage '{stage_name}' to status '{status}'")
