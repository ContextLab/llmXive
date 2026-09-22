import os
import hashlib
from pathlib import Path
from typing import List, Tuple
import fnmatch

def calculate_directory_hash(root_path: Path, exclude_patterns: List[str] = None) -> str:
    """
    Calculates a SHA256 hash of the directory structure and file contents.
    Excludes patterns like __pycache__, .git, etc.
    """
    if exclude_patterns is None:
        exclude_patterns = ["__pycache__", "*.pyc", ".git", ".DS_Store"]

    hasher = hashlib.sha256()
    root_str = str(root_path.resolve())

    # Walk directory
    # We need a deterministic order, so we sort files and dirs
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Sort in-place to ensure deterministic traversal order
        dirnames.sort()
        filenames.sort()

        # Filter out excluded directories
        dirnames[:] = [d for d in dirnames if not any(fnmatch.fnmatch(d, p) for p in exclude_patterns)]

        # Filter files
        filtered_files = [f for f in filenames if not any(fnmatch.fnmatch(f, p) for p in exclude_patterns)]

        # Hash directory entry (relative path)
        rel_dir = os.path.relpath(dirpath, root_path)
        hasher.update(rel_dir.encode('utf-8'))
        hasher.update(b'\n')

        for filename in filtered_files:
            file_path = Path(dirpath) / filename
            rel_file = os.path.relpath(file_path, root_path)
            
            # Hash file path
            hasher.update(rel_file.encode('utf-8'))
            hasher.update(b':')
            
            # Hash file content
            try:
                with open(file_path, 'rb') as f:
                    # Read in chunks for large files
                    while chunk := f.read(8192):
                        hasher.update(chunk)
            except (IOError, OSError):
                # If we can't read a file, we still hash the path but note it?
                # For this task, we assume readable files or skip silently
                pass
            
            hasher.update(b'\n')

    return hasher.hexdigest()

def update_project_state(project_root: Path, project_id: str, new_hash: str):
    """
    Updates the state/projects/{project_id}.yaml file with the new hash.
    """
    state_dir = project_root / "state" / "projects"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / f"{project_id}.yaml"
    
    # Simple append/update logic for the hash line if file exists
    if state_file.exists():
        lines = state_file.read_text().splitlines()
        new_lines = []
        hash_updated = False
        for line in lines:
            if line.startswith("structure_hash:"):
                new_lines.append(f"structure_hash: {new_hash}")
                hash_updated = True
            else:
                new_lines.append(line)
        
        if not hash_updated:
            new_lines.append(f"structure_hash: {new_hash}")
        
        state_file.write_text('\n'.join(new_lines) + '\n')
    else:
        # Create new file
        content = f"""project_id: {project_id}
structure_hash: {new_hash}
"""
        state_file.write_text(content)