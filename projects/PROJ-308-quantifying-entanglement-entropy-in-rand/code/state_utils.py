"""
State Utilities Module.

Provides functions for managing project state, including directory structure,
checksums, and artifact registration.
"""
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

# Project root relative to this module
PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
PROJECTS_DIR = STATE_DIR / "projects"
ARTIFACTS_DIR = STATE_DIR / "artifacts"
CHECKSUMS_FILE = PROJECTS_DIR / "checksums.json"
STATE_FILE = PROJECTS_DIR / "state.json"

def ensure_state_structure():
    """Create the required state directory structure if it doesn't exist."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

def compute_file_checksum(file_path: Path) -> str:
    """
    Compute SHA-256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hex digest of the file's checksum.
    """
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def compute_directory_checksum(dir_path: Path) -> str:
    """
    Compute a combined checksum of all files in a directory.

    Args:
        dir_path: Path to the directory.

    Returns:
        Hex digest of the combined checksum.
    """
    sha256 = hashlib.sha256()
    # Sort files for deterministic order
    files = sorted(dir_path.rglob('*'))
    for file_path in files:
        if file_path.is_file():
          # Include relative path in checksum to detect renames/moves
          rel_path = file_path.relative_to(dir_path)
          sha256.update(str(rel_path).encode('utf-8'))
          with open(file_path, 'rb') as f:
              for chunk in iter(lambda: f.read(8192), b''):
                  sha256.update(chunk)
    return sha256.hexdigest()

def load_project_state() -> Dict[str, Any]:
    """
    Load the current project state from disk.

    Returns:
        Dict representing the project state.
    """
    ensure_state_structure()
    if not STATE_FILE.exists():
        return {
            "project_id": "PROJ-308-quantifying-entanglement-entropy-in-rand",
            "version": "0.1.0",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "artifacts": {},
            "checksums": {}
        }
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {
            "project_id": "PROJ-308-quantifying-entanglement-entropy-in-rand",
            "version": "0.1.0",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "artifacts": {},
            "checksums": {}
        }

def save_project_state(state: Dict[str, Any]):
    """
    Save the project state to disk.

    Args:
        state: Dict representing the project state.
    """
    ensure_state_structure()
    state["last_updated"] = datetime.now().isoformat()
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def register_artifact(
    artifact_path: Path,
    artifact_type: str,
    description: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Register an artifact in the project state and compute its checksum.

    Args:
        artifact_path: Path to the artifact file.
        artifact_type: Type of artifact (e.g., 'csv', 'png', 'txt').
        description: Human-readable description.
        metadata: Optional additional metadata.
    """
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")

    state = load_project_state()
    rel_path = str(artifact_path.relative_to(PROJECT_ROOT))
    checksum = compute_file_checksum(artifact_path)

    artifact_info = {
        "path": rel_path,
        "type": artifact_type,
        "description": description,
        "checksum": checksum,
        "size_bytes": artifact_path.stat().st_size,
        "created_at": datetime.now().isoformat(),
        "metadata": metadata or {}
    }

    state["artifacts"][rel_path] = artifact_info
    state["checksums"][rel_path] = checksum
    save_project_state(state)

def verify_artifact_integrity(artifact_path: Path) -> bool:
    """
    Verify that an artifact's checksum matches the recorded one.

    Args:
        artifact_path: Path to the artifact file.

    Returns:
        True if checksum matches, False otherwise.
    """
    if not artifact_path.exists():
        return False

    state = load_project_state()
    rel_path = str(artifact_path.relative_to(PROJECT_ROOT))

    if rel_path not in state.get("checksums", {}):
        return False

    current_checksum = compute_file_checksum(artifact_path)
    recorded_checksum = state["checksums"][rel_path]

    return current_checksum == recorded_checksum

def get_artifact_summary(artifact_path: Path) -> Optional[Dict[str, Any]]:
    """
    Get summary information for a registered artifact.

    Args:
        artifact_path: Path to the artifact file.

    Returns:
        Dict with artifact info or None if not registered.
    """
    state = load_project_state()
    rel_path = str(artifact_path.relative_to(PROJECT_ROOT))
    return state.get("artifacts", {}).get(rel_path)

def generate_state_report(output_path: Optional[Path] = None) -> str:
    """
    Generate a text report of the current project state.

    Args:
        output_path: Optional path to write the report. If None, returns string.

    Returns:
        Report as a string.
    """
    state = load_project_state()
    report_lines = [
        f"Project State Report",
        f"====================",
        f"Project ID: {state.get('project_id', 'Unknown')}",
        f"Version: {state.get('version', 'Unknown')}",
        f"Created: {state.get('created_at', 'Unknown')}",
        f"Last Updated: {state.get('last_updated', 'Unknown')}",
        f"",
        f"Registered Artifacts ({len(state.get('artifacts', {}))}):",
        "-" * 40
    ]

    for path, info in state.get("artifacts", {}).items():
        report_lines.append(f"  - {path}")
        report_lines.append(f"    Type: {info.get('type', 'Unknown')}")
        report_lines.append(f"    Size: {info.get('size_bytes', 0)} bytes")
        report_lines.append(f"    Checksum: {info.get('checksum', 'Unknown')[:16]}...")
        report_lines.append(f"    Description: {info.get('description', 'N/A')}")
        report_lines.append("")

    report = "\n".join(report_lines)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(report)

    return report
