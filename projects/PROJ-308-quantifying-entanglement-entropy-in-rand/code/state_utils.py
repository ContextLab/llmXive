import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

# Ensure the project root is in the path for relative imports if run as script
# but rely on standard package imports when run as module.
try:
    from config import get_default_config
except ImportError:
    # Fallback for direct execution if path is not set up correctly
    pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_ROOT / "state"
PROJECTS_DIR = STATE_DIR / "projects"
ARTIFACTS_DIR = STATE_DIR / "artifacts"

def ensure_state_structure() -> None:
    """
    Creates the necessary directory structure for state management.
    Specifically creates:
    - state/
    - state/projects/
    - state/artifacts/
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

def compute_file_checksum(file_path: Path) -> str:
    """
    Computes the SHA-256 checksum of a file.
    Raises FileNotFoundError if the file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for checksum: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def compute_directory_checksum(dir_path: Path) -> str:
    """
    Computes a checksum for a directory by hashing the sorted list of 
    (relative_path, file_checksum) tuples.
    """
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")
    
    entries = []
    for file_path in sorted(dir_path.rglob("*")):
        if file_path.is_file():
            rel_path = file_path.relative_to(dir_path)
            file_checksum = compute_file_checksum(file_path)
            entries.append(f"{rel_path}:{file_checksum}")
    
    content = "\n".join(entries)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

def load_project_state(project_id: str) -> Dict[str, Any]:
    """
    Loads the state YAML (stored as JSON for Python compatibility in this task)
    for a specific project.
    """
    state_file = PROJECTS_DIR / f"{project_id}.json"
    if not state_file.exists():
        return {
            "project_id": project_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "artifacts": {},
            "metadata": {}
        }
    
    with open(state_file, "r") as f:
        return json.load(f)

def save_project_state(project_id: str, state: Dict[str, Any]) -> None:
    """
    Saves the state for a specific project.
    Updates the 'updated_at' timestamp.
    """
    state_file = PROJECTS_DIR / f"{project_id}.json"
    state["updated_at"] = datetime.now().isoformat()
    
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)

def register_artifact(project_id: str, artifact_name: str, artifact_path: Path) -> None:
    """
    Registers an artifact in the project state, computing and storing its checksum.
    """
    if not artifact_path.exists():
        raise FileNotFoundError(f"Cannot register non-existent artifact: {artifact_path}")
    
    state = load_project_state(project_id)
    
    checksum = compute_file_checksum(artifact_path)
    
    artifact_entry = {
        "path": str(artifact_path.relative_to(PROJECT_ROOT)),
        "checksum": checksum,
        "registered_at": datetime.now().isoformat(),
        "size_bytes": artifact_path.stat().st_size
    }
    
    state["artifacts"][artifact_name] = artifact_entry
    save_project_state(project_id, state)

def verify_artifact_integrity(project_id: str, artifact_name: str) -> bool:
    """
    Verifies that an artifact's current checksum matches the stored checksum.
    Returns True if valid, False otherwise.
    """
    state = load_project_state(project_id)
    
    if artifact_name not in state["artifacts"]:
        return False
    
    stored_entry = state["artifacts"][artifact_name]
    stored_checksum = stored_entry["checksum"]
    artifact_path = PROJECT_ROOT / stored_entry["path"]
    
    if not artifact_path.exists():
        return False
    
    current_checksum = compute_file_checksum(artifact_path)
    return current_checksum == stored_checksum

def get_artifact_summary(project_id: str) -> Dict[str, Any]:
    """
    Returns a summary of all registered artifacts for a project.
    """
    state = load_project_state(project_id)
    return {
        "project_id": project_id,
        "artifact_count": len(state["artifacts"]),
        "artifacts": list(state["artifacts"].keys()),
        "last_updated": state.get("updated_at")
    }

def generate_state_report(project_id: str) -> Dict[str, Any]:
    """
    Generates a comprehensive state report including directory checksums.
    """
    state = load_project_state(project_id)
    
    # Compute checksums for registered artifacts
    integrity_status = {}
    for name, entry in state["artifacts"].items():
        path = PROJECT_ROOT / entry["path"]
        if path.exists():
            integrity_status[name] = {
                "valid": compute_file_checksum(path) == entry["checksum"],
                "size": entry["size_bytes"]
            }
        else:
            integrity_status[name] = {"valid": False, "size": 0, "error": "missing"}
    
    return {
        "project_id": project_id,
        "state_version": "1.0",
        "generated_at": datetime.now().isoformat(),
        "artifacts": integrity_status,
        "total_artifacts": len(state["artifacts"])
    }
