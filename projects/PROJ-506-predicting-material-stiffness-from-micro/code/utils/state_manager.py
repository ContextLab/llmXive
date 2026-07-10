import os
import yaml
import hashlib
from datetime import datetime
from pathlib import Path

def load_state_file(path: Path) -> dict:
    """Load a YAML state file, returning an empty dict if it doesn't exist."""
    if not path.exists():
        return {}
    with open(path, 'r') as f:
        return yaml.safe_load(f) or {}

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    if not file_path.exists():
        return ""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_project_state(
    project_id: str,
    state_dir: Path,
    artifact_paths: list[Path],
    description: str
) -> None:
    """
    Updates the project state YAML file with new artifact hashes and timestamp.
    
    Args:
        project_id: The project identifier (e.g., 'PROJ-506...')
        state_dir: Directory containing the 'state' folder structure
        artifact_paths: List of file paths to include in the artifact_hashes
        description: Human-readable description of the update
    """
    state_file = state_dir / "projects" / f"{project_id}.yaml"
    
    # Ensure directory exists
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing state
    state = load_state_file(state_file)
    
    # Initialize project entry if missing
    if project_id not in state:
        state[project_id] = {
            "artifact_hashes": {},
            "last_updated": None,
            "history": []
        }
    
    project_entry = state[project_id]
    
    # Compute hashes for new artifacts
    new_hashes = {}
    for p in artifact_paths:
        if p.exists():
          new_hashes[str(p.relative_to(state_dir.parent))] = compute_file_hash(p)
        else:
          new_hashes[str(p.relative_to(state_dir.parent))] = "MISSING"
    
    # Update project entry
    project_entry["artifact_hashes"].update(new_hashes)
    project_entry["last_updated"] = datetime.utcnow().isoformat() + "Z"
    project_entry["history"].append({
        "timestamp": project_entry["last_updated"],
        "description": description,
        "updated_artifacts": list(new_hashes.keys())
    })
    
    # Write back to file
    with open(state_file, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
