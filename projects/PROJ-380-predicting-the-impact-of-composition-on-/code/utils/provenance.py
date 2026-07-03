import hashlib
import os
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# Project root relative to this file
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# State directory path (matches T006 specification)
_STATE_DIR = _PROJECT_ROOT / "state" / "projects"

def ensure_state_directory() -> Path:
    """Ensure the state directory exists."""
    _STATE_DIR.mkdir(parents=True, exist_ok=True)
    return _STATE_DIR

def get_provenance_state_file(project_id: str = "PROJ-380-predicting-the-impact-of-composition-on-") -> Path:
    """Return the path to the canonical state YAML file for the project."""
    # Sanitize project_id to be filesystem safe (basic)
    safe_id = "".join(c if c.isalnum() or c in "-_." else "_" for c in project_id)
    return _STATE_DIR / f"{safe_id}.yaml"

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for checksum: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_existing_state(state_file: Path) -> Dict[str, Any]:
    """Load existing state file or return a fresh structure if it doesn't exist."""
    if state_file.exists():
        with open(state_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {
        "project_id": state_file.stem,
        "created_at": datetime.utcnow().isoformat(),
        "artifacts": []
    }

def save_state(state_file: Path, state: Dict[str, Any]) -> None:
    """Save the state dictionary to the YAML file."""
    with open(state_file, "w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def record_artifact(
    file_path: Path,
    state_file: Optional[Path] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Compute checksum for a file and record it in the project's state file.
    This implements Constitution Principle V: deterministic reproducibility via checksums.
    
    Args:
        file_path: Path to the artifact file.
        state_file: Optional override for the state file path. Defaults to project default.
        description: Optional human-readable description.
        tags: Optional list of tags for categorization.
    
    Returns:
        The record dictionary added to the state.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot record artifact: file not found at {file_path}")
    
    if state_file is None:
        # Default project state file
        state_file = get_provenance_state_file()
    
    # Ensure directory exists
    ensure_state_directory()
    
    # Compute checksum
    checksum = compute_file_checksum(file_path)
    
    # Load existing state
    state = load_existing_state(state_file)
    
    # Create record
    record = {
        "path": str(file_path.relative_to(_PROJECT_ROOT)),
        "checksum": checksum,
        "recorded_at": datetime.utcnow().isoformat(),
    }
    
    if description:
        record["description"] = description
    if tags:
        record["tags"] = tags
    
    # Append to state
    if "artifacts" not in state:
        state["artifacts"] = []
    state["artifacts"].append(record)
    
    # Save updated state
    save_state(state_file, state)
    
    return record

def verify_artifact(file_path: Path, state_file: Optional[Path] = None) -> bool:
    """
    Verify that a file's current checksum matches the last recorded checksum in the state.
    
    Returns:
        True if checksum matches, False if mismatch or record not found.
    """
    if not file_path.exists():
        return False
    
    if state_file is None:
        state_file = get_provenance_state_file()
    
    if not state_file.exists():
        return False
    
    state = load_existing_state(state_file)
    rel_path = str(file_path.relative_to(_PROJECT_ROOT))
    
    # Find record
    record = None
    for artifact in state.get("artifacts", []):
        if artifact.get("path") == rel_path:
            record = artifact
            break
    
    if not record:
        return False
    
    expected_checksum = record.get("checksum")
    if not expected_checksum:
        return False
    
    actual_checksum = compute_file_checksum(file_path)
    return actual_checksum == expected_checksum

def list_artifacts(state_file: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Return a list of all recorded artifacts from the state file."""
    if state_file is None:
        state_file = get_provenance_state_file()
    
    if not state_file.exists():
        return []
    
    state = load_existing_state(state_file)
    return state.get("artifacts", [])