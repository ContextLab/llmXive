"""
Versioning module for llmXive automated science pipeline.

Computes SHA256 hashes of artifacts in data/ and code/ directories
and updates the project state file.
"""
import hashlib
import os
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

from config import DATA_ROOT


def compute_file_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def hash_directory(directory: Path, base_path: Path) -> Dict[str, str]:
    """
    Recursively compute SHA256 hashes for all files in a directory.
    
    Returns a dictionary mapping relative file paths to their hashes.
    """
    hashes = {}
    if not directory.exists():
        return hashes
        
    for file_path in sorted(directory.rglob("*")):
        if file_path.is_file():
            rel_path = file_path.relative_to(base_path)
            hashes[str(rel_path)] = compute_file_sha256(file_path)
    
    return hashes


def update_state_file(
    project_id: str, 
    data_hashes: Dict[str, str], 
    code_hashes: Dict[str, str]
) -> None:
    """
    Update the project state YAML file with new artifact hashes.
    
    Args:
        project_id: The project identifier (e.g., 'PROJ-407-predicting-plant-herbivore-resistance-fr')
        data_hashes: Dictionary of data artifact hashes
        code_hashes: Dictionary of code artifact hashes
    """
    state_root = Path("state/projects")
    state_root.mkdir(parents=True, exist_ok=True)
    
    state_file = state_root / f"{project_id}.yaml"
    
    # Load existing state or create new
    if state_file.exists():
        with open(state_file, "r") as f:
            state_data = yaml.safe_load(f) or {}
    else:
        state_data = {
            "project_id": project_id,
            "artifact_hashes": {},
            "updated_at": None
        }
    
    # Update artifact hashes
    state_data["artifact_hashes"] = {
        "data": data_hashes,
        "code": code_hashes
    }
    
    # Update timestamp
    state_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Write back
    with open(state_file, "w") as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)


def main() -> None:
    """
    Main entry point for versioning task.
    
    Computes hashes for data/ and code/ directories and updates
    the project state file.
    """
    project_id = "PROJ-407-predicting-plant-herbivore-resistance-fr"
    root_path = Path.cwd()
    
    # Define directories to hash
    data_dir = root_path / DATA_ROOT
    code_dir = root_path / "code"
    
    # Compute hashes
    data_hashes = hash_directory(data_dir, root_path)
    code_hashes = hash_directory(code_dir, root_path)
    
    # Update state file
    update_state_file(project_id, data_hashes, code_hashes)
    
    print(f"Updated state file for project {project_id}")
    print(f"Data artifacts hashed: {len(data_hashes)}")
    print(f"Code artifacts hashed: {len(code_hashes)}")


if __name__ == "__main__":
    main()
