"""
State management utilities for versioning and checksum tracking.

Implements Constitution Principle IV: Audit Trail & Reproducibility.
"""
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import yaml

PROJECT_ID = "PROJ-308-quantifying-entanglement-entropy-in-rand"
STATE_DIR = Path("state")
PROJECTS_DIR = STATE_DIR / "projects"
ARTIFACTS_DIR = STATE_DIR / "artifacts"

def ensure_state_structure() -> None:
    """Create the state directory structure if it doesn't exist."""
    STATE_DIR.mkdir(exist_ok=True)
    PROJECTS_DIR.mkdir(exist_ok=True)
    ARTIFACTS_DIR.mkdir(exist_ok=True)

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_directory_checksum(dir_path: Path, pattern: str = "*") -> str:
    """
    Compute a deterministic checksum for a directory based on its contents.
    Files are processed in sorted order for reproducibility.
    """
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")
    
    sha256_hash = hashlib.sha256()
    files = sorted(dir_path.glob(pattern))
    
    for file_path in files:
        if file_path.is_file():
          # Include relative path in hash to detect file renames/moves
          rel_path = str(file_path.relative_to(dir_path))
          sha256_hash.update(rel_path.encode('utf-8'))
          sha256_hash.update(compute_file_checksum(file_path).encode('utf-8'))
    
    return sha256_hash.hexdigest()

def load_project_state() -> Dict[str, Any]:
    """Load the current project state YAML or create a new one."""
    ensure_state_structure()
    state_file = PROJECTS_DIR / f"{PROJECT_ID}.yaml"
    
    if state_file.exists():
        with open(state_file, 'r') as f:
            return yaml.safe_load(f)
    
    # Initialize new project state
    return {
        "project_id": PROJECT_ID,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "checksums": {},
        "artifacts": [],
        "metadata": {
            "status": "active",
            "description": "Quantifying Entanglement Entropy in Randomly Perturbed Quantum Spin Chains"
        }
    }

def save_project_state(state: Dict[str, Any]) -> None:
    """Save the project state to YAML."""
    ensure_state_structure()
    state_file = PROJECTS_DIR / f"{PROJECT_ID}.yaml"
    
    state["updated_at"] = datetime.utcnow().isoformat()
    
    with open(state_file, 'w') as f:
        yaml.safe_dump(state, f, default_flow_style=False, sort_keys=False)

def register_artifact(
    artifact_path: Path,
    artifact_type: str,
    description: str = "",
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Register an artifact in the project state with its checksum.
    
    Args:
        artifact_path: Path to the artifact file (relative to project root)
        artifact_type: Type of artifact (e.g., 'data', 'code', 'figure', 'config')
        description: Human-readable description
        metadata: Additional metadata to store
    
    Returns:
        Dictionary containing the artifact registration details
    """
    ensure_state_structure()
    
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")
    
    state = load_project_state()
    
    # Compute checksum
    checksum = compute_file_checksum(artifact_path)
    file_size = artifact_path.stat().st_size
    
    # Create artifact entry
    artifact_entry = {
        "path": str(artifact_path),
        "type": artifact_type,
        "checksum": checksum,
        "size_bytes": file_size,
        "registered_at": datetime.utcnow().isoformat(),
        "description": description,
        "metadata": metadata or {}
    }
    
    # Update state
    state["artifacts"].append(artifact_entry)
    
    # Update checksums dictionary for quick lookup
    checksum_key = f"{artifact_type}:{artifact_path}"
    state["checksums"][checksum_key] = checksum
    
    save_project_state(state)
    
    return artifact_entry

def verify_artifact_integrity(artifact_path: Path) -> bool:
    """
    Verify that an artifact's current checksum matches the stored checksum.
    
    Returns:
        True if checksum matches, False otherwise
    """
    ensure_state_structure()
    state = load_project_state()
    
    if not artifact_path.exists():
        return False
    
    current_checksum = compute_file_checksum(artifact_path)
    checksum_key = f"unknown:{artifact_path}"  # Fallback key
    
    # Try to find the checksum in the state
    found_checksum = None
    for entry in state.get("artifacts", []):
        if entry["path"] == str(artifact_path):
            found_checksum = entry["checksum"]
            break
    
    if found_checksum is None:
        return False
    
    return current_checksum == found_checksum

def get_artifact_summary() -> List[Dict[str, Any]]:
    """Get a summary of all registered artifacts."""
    state = load_project_state()
    return state.get("artifacts", [])

def generate_state_report() -> str:
    """Generate a human-readable state report."""
    state = load_project_state()
    artifacts = state.get("artifacts", [])
    
    report_lines = [
        f"Project State Report: {state['project_id']}",
        f"Version: {state['version']}",
        f"Created: {state['created_at']}",
        f"Last Updated: {state['updated_at']}",
        f"Total Artifacts: {len(artifacts)}",
        "",
        "Registered Artifacts:"
    ]
    
    for artifact in artifacts:
        report_lines.append(
            f"  - {artifact['path']} ({artifact['type']}) "
            f"[Checksum: {artifact['checksum'][:16]}...]"
        )
    
    return "\n".join(report_lines)
