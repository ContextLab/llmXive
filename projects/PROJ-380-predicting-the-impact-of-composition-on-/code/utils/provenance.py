"""
Provenance tracking module for llmXive pipeline.

Implements Constitution Principle V: All artifacts must be checksummed and
recorded in a canonical state file to ensure reproducibility and auditability.
"""
import hashlib
import os
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# Project-specific constants
PROJECT_ID = "PROJ-380-predicting-the-impact-of-composition-on-"
STATE_DIR = Path("state") / "projects"
STATE_FILENAME = f"{PROJECT_ID}.yaml"

# Ensure the state directory exists
def ensure_state_directory() -> Path:
    """Create the state directory if it doesn't exist."""
    state_dir = STATE_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir

def get_provenance_state_file() -> Path:
    """Return the path to the canonical provenance state file."""
    ensure_state_directory()
    return STATE_DIR / STATE_FILENAME

def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file.
    
    Args:
        file_path: Path to the file to checksum
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Hexadecimal string of the checksum
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the algorithm is not supported
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)
            
    return hash_func.hexdigest()

def load_existing_state() -> Dict[str, Any]:
    """
    Load the existing provenance state from disk.
    
    Returns:
        Dictionary containing the current state, or empty structure if file doesn't exist
    """
    state_file = get_provenance_state_file()
    
    if not state_file.exists():
        return {
            "project_id": PROJECT_ID,
            "created_at": datetime.utcnow().isoformat(),
            "artifacts": {}
        }
        
    with open(state_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_state(state: Dict[str, Any]) -> None:
    """
    Save the provenance state to disk.
    
    Args:
        state: The state dictionary to save
    """
    state_file = get_provenance_state_file()
    with open(state_file, "w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def record_artifact(
    artifact_path: Path,
    artifact_type: str,
    description: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Record an artifact in the provenance state.
    
    Args:
        artifact_path: Path to the artifact file
        artifact_type: Type of artifact (e.g., 'data', 'model', 'script')
        description: Optional description of the artifact
        metadata: Optional additional metadata
        
    Returns:
        The artifact record that was added to the state
        
    Raises:
        FileNotFoundError: If the artifact file doesn't exist
    """
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")
        
    # Compute checksum
    checksum = compute_file_checksum(artifact_path)
    
    # Get relative path from project root
    try:
        relative_path = artifact_path.relative_to(Path.cwd())
    except ValueError:
        relative_path = artifact_path
        
    # Create artifact record
    artifact_record = {
        "path": str(relative_path),
        "type": artifact_type,
        "checksum": checksum,
        "algorithm": "sha256",
        "recorded_at": datetime.utcnow().isoformat(),
        "description": description or "",
        "metadata": metadata or {}
    }
    
    # Load existing state
    state = load_existing_state()
    
    # Add to artifacts
    state_key = str(relative_path)
    state["artifacts"][state_key] = artifact_record
    
    # Save updated state
    save_state(state)
    
    return artifact_record

def verify_artifact(artifact_path: Path) -> bool:
    """
    Verify an artifact's checksum against the recorded state.
    
    Args:
        artifact_path: Path to the artifact to verify
        
    Returns:
        True if the artifact's checksum matches the recorded one, False otherwise
        
    Raises:
        FileNotFoundError: If the artifact or state file doesn't exist
    """
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")
        
    # Load state
    state = load_existing_state()
    
    # Get relative path
    try:
        relative_path = artifact_path.relative_to(Path.cwd())
    except ValueError:
        relative_path = artifact_path
        
    state_key = str(relative_path)
    
    if state_key not in state.get("artifacts", {}):
        # Artifact not previously recorded
        return False
        
    # Get recorded checksum
    recorded_checksum = state["artifacts"][state_key]["checksum"]
    
    # Compute current checksum
    current_checksum = compute_file_checksum(artifact_path)
    
    return recorded_checksum == current_checksum

def list_artifacts(artifact_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all recorded artifacts, optionally filtered by type.
    
    Args:
        artifact_type: Optional filter for artifact type
        
    Returns:
        List of artifact records
    """
    state = load_existing_state()
    artifacts = list(state.get("artifacts", {}).values())
    
    if artifact_type:
        artifacts = [a for a in artifacts if a.get("type") == artifact_type]
        
    return artifacts
