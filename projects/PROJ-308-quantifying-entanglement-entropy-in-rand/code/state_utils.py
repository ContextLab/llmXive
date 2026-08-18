"""
State Utilities for PROJ-308.

Handles state directory structure, checksums, and artifact registration.
"""
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
PROJECTS_DIR = STATE_DIR / "projects"
STATE_FILE = PROJECTS_DIR / "PROJ-308-quantifying-entanglement-entropy-in-rand.yaml"

def ensure_state_structure():
    """
    Ensure the state directory structure exists.
    Creates: state/, state/projects/
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

def compute_file_checksum(file_path: Path) -> str:
    """
    Compute SHA256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hex string of SHA256 hash.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def compute_directory_checksum(dir_path: Path) -> str:
    """
    Compute a combined checksum for all files in a directory.

    Args:
        dir_path: Path to the directory.

    Returns:
        Hex string of combined SHA256 hash.
    """
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")

    sha256_hash = hashlib.sha256()
    # Sort files for deterministic ordering
    files = sorted(dir_path.rglob("*"))
    for file_path in files:
        if file_path.is_file():
            relative_path = file_path.relative_to(dir_path)
            sha256_hash.update(relative_path.as_posix().encode())
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def load_project_state() -> Dict[str, Any]:
    """
    Load the project state file.

    Returns:
        Dict containing project state.
    """
    if not STATE_FILE.exists():
        return {
            "project_id": "PROJ-308-quantifying-entanglement-entropy-in-rand",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "artifacts": {},
            "checksums": {}
        }

    with open(STATE_FILE, 'r') as f:
        return json.load(f)

def save_project_state(state: Dict[str, Any]):
    """
    Save the project state file.

    Args:
        state: Dict containing project state.
    """
    ensure_state_structure()
    state["updated_at"] = datetime.utcnow().isoformat()
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def register_artifact(artifact_path: Path, artifact_name: str, artifact_type: str = "file"):
    """
    Register an artifact in the project state.

    Args:
        artifact_path: Path to the artifact file.
        artifact_name: Name to register the artifact under.
        artifact_type: Type of artifact (file, directory, etc.).
    """
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")

    state = load_project_state()

    if artifact_type == "file":
        checksum = compute_file_checksum(artifact_path)
    elif artifact_type == "directory":
        checksum = compute_directory_checksum(artifact_path)
    else:
        raise ValueError(f"Unknown artifact type: {artifact_type}")

    state["artifacts"][artifact_name] = {
        "path": str(artifact_path.relative_to(PROJECT_ROOT)),
        "type": artifact_type,
        "checksum": checksum,
        "registered_at": datetime.utcnow().isoformat()
    }
    state["checksums"][artifact_name] = checksum

    save_project_state(state)

def verify_artifact_integrity(artifact_name: str) -> bool:
    """
    Verify the integrity of a registered artifact.

    Args:
        artifact_name: Name of the artifact to verify.

    Returns:
        True if integrity check passes, False otherwise.
    """
    state = load_project_state()
    if artifact_name not in state["artifacts"]:
        return False

    artifact_info = state["artifacts"][artifact_name]
    registered_checksum = artifact_info["checksum"]
    artifact_path = PROJECT_ROOT / artifact_info["path"]

    if not artifact_path.exists():
        return False

    if artifact_info["type"] == "file":
        current_checksum = compute_file_checksum(artifact_path)
    elif artifact_info["type"] == "directory":
        current_checksum = compute_directory_checksum(artifact_path)
    else:
        return False

    return current_checksum == registered_checksum

def get_artifact_summary() -> Dict[str, Any]:
    """
    Get a summary of all registered artifacts.

    Returns:
        Dict mapping artifact names to their info.
    """
    state = load_project_state()
    return state.get("artifacts", {})

def generate_state_report() -> Dict[str, Any]:
    """
    Generate a comprehensive state report.

    Returns:
        Dict containing state report with artifacts, checksums, and unresolved summary.
    """
    from state_manager import get_unresolved_summary

    state = load_project_state()
    unresolved_summary = get_unresolved_summary()

    report = {
        "project_id": state["project_id"],
        "created_at": state.get("created_at"),
        "updated_at": state.get("updated_at"),
        "artifact_count": len(state.get("artifacts", {})),
        "artifacts": state.get("artifacts", {}),
        "unresolved_summary": unresolved_summary
    }
    return report
