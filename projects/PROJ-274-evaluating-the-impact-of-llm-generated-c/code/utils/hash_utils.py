import os
import hashlib
from pathlib import Path
from typing import List, Tuple

def calculate_directory_hash(root_dir: Path) -> str:
    """
    Calculates a SHA256 hash of the entire directory tree structure and file contents.
    This provides a unique fingerprint for the project state.
    """
    sha256_hash = hashlib.sha256()
    
    # Walk the directory tree
    for path in sorted(root_dir.rglob("*")):
        if path.is_file():
            # Include relative path in the hash
            rel_path = path.relative_to(root_dir)
            sha256_hash.update(str(rel_path).encode('utf-8'))
            
            # Include file content hash
            try:
                with open(path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        sha256_hash.update(chunk)
            except (PermissionError, FileNotFoundError):
                # Skip files we can't read
                continue
        elif path.is_dir():
            # Include directory path
            rel_path = path.relative_to(root_dir)
            sha256_hash.update(str(rel_path).encode('utf-8'))
            sha256_hash.update(b'/') # Directory marker
            
    return sha256_hash.hexdigest()

def update_project_state(project_root: Path, project_name: str, new_hash: str):
    """
    Updates the state/projects/{project_name}.yaml file with the new hash.
    """
    state_dir = project_root / "state" / "projects"
    state_dir.mkdir(parents=True, exist_ok=True)
    
    state_file = state_dir / f"{project_name}.yaml"
    
    content = f"""project_name: {project_name}
initial_hash: {new_hash}
last_updated: auto-generated
"""
    with open(state_file, "w") as f:
        f.write(content)
    
    return state_file