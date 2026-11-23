import os
import hashlib
from pathlib import Path
from typing import List, Tuple
import fnmatch

def calculate_directory_hash(directory_path: str, algorithm: str = 'sha256') -> str:
    """
    Calculate a SHA256 hash of the entire directory tree.
    Iterates files in sorted order to ensure deterministic hashing.
    """
    hasher = hashlib.sha256()
    root = Path(directory_path)
    
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {directory_path}")

    # Walk directory, sort for determinism
    for dirpath, dirnames, filenames in os.walk(root):
        # Sort dirs and files to ensure consistent traversal order
        dirnames.sort()
        filenames.sort()
        
        for filename in filenames:
            file_path = Path(dirpath) / filename
            # Calculate relative path for inclusion in hash
            rel_path = file_path.relative_to(root)
            hasher.update(str(rel_path).encode('utf-8'))
            
            try:
                with open(file_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b''):
                        hasher.update(chunk)
            except (IOError, OSError):
                # Skip files we can't read (permissions, etc)
                continue
    
    return hasher.hexdigest()

def update_project_state(project_root: str, project_id: str, hash_value: str, state_dir: str = 'state') -> None:
    """
    Update the project state YAML file with the new directory hash.
    Creates the state directory and file if they don't exist.
    """
    import json
    from datetime import datetime

    state_path = Path(project_root) / state_dir
    state_path.mkdir(parents=True, exist_ok=True)
    
    state_file = state_path / f"{project_id}.yaml"
    
    # Load existing state or create new
    if state_file.exists():
        import yaml
        with open(state_file, 'r') as f:
            try:
                state_data = yaml.safe_load(f) or {}
            except yaml.YAMLError:
                state_data = {}
    else:
        state_data = {}

    # Ensure projects key exists
    if 'projects' not in state_data:
        state_data['projects'] = {}
    
    # Update project hash
    state_data['projects'][project_id] = {
        'initial_hash': hash_value,
        'last_updated': datetime.utcnow().isoformat() + 'Z',
        'status': 'initialized'
    }

    # Write back
    import yaml
    with open(state_file, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)

def main():
    """
    CLI entry point for directory hashing and state update.
    Usage: python code/utils/hash_utils.py --project-root <path> --project-id <id>
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Calculate directory hash and update project state')
    parser.add_argument('--project-root', required=True, help='Path to project root directory')
    parser.add_argument('--project-id', required=True, help='Project identifier (e.g., PROJ-274)')
    parser.add_argument('--state-dir', default='state', help='Directory for state files')
    
    args = parser.parse_args()
    
    project_root = Path(args.project_root).resolve()
    project_id = args.project_id
    state_dir = args.state_dir
    
    try:
        print(f"Calculating hash for: {project_root}")
        directory_hash = calculate_directory_hash(str(project_root))
        print(f"Directory Hash (SHA256): {directory_hash}")
        
        print(f"Updating project state for: {project_id}")
        update_project_state(str(project_root), project_id, directory_hash, state_dir)
        
        state_file = project_root / state_dir / f"{project_id}.yaml"
        print(f"State file updated: {state_file}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    import sys
    main()
