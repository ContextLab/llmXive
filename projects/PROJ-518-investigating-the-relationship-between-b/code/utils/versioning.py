import hashlib
import os
from pathlib import Path
from typing import Dict
import yaml
from config import get_config

def hash_file(path: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_state_file() -> None:
    """
    Compute SHA-256 hashes for all tracked project files and write them
    to the state YAML file.
    
    Reads configuration from config.py to determine:
    - state_file_path: where to write the YAML
    - tracked_extensions: list of file extensions to include
    
    Writes a YAML file with a 'files' dictionary mapping relative paths
    to their SHA-256 hashes.
    """
    config = get_config()
    state_file_path = Path(config.STATE_FILE_PATH)
    state_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Define tracked extensions
    tracked_extensions = ['.py', '.yaml', '.yml', '.json', '.csv', '.txt', '.md']
    
    # Collect all tracked files
    project_root = Path(__file__).resolve().parent.parent
    files_to_hash: Dict[str, str] = {}
    
    for root, _, files in os.walk(project_root):
        # Skip certain directories
        root_path = Path(root)
        if any(skip in root_path.parts for skip in ['__pycache__', '.git', 'venv', '.venv', 'node_modules']):
            continue
            
        for file in files:
            if any(file.endswith(ext) for ext in tracked_extensions):
                file_path = Path(root) / file
                rel_path = str(file_path.relative_to(project_root))
                abs_path = str(file_path.absolute())
                
                if os.path.isfile(abs_path):
                    files_to_hash[rel_path] = abs_path
    
    # Compute hashes and build state dictionary
    state_data = {
        'state_version': '1.0',
        'project_id': 'PROJ-518-investigating-the-relationship-between-b',
        'files': {}
    }
    
    for rel_path, abs_path in files_to_hash.items():
        try:
            file_hash = hash_file(abs_path)
            state_data['files'][rel_path] = file_hash
        except (IOError, OSError) as e:
            # Log warning but continue processing other files
            print(f"Warning: Could not hash {rel_path}: {e}", file=sys.stderr)
    
    # Write state file
    with open(state_file_path, 'w', encoding='utf-8') as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
