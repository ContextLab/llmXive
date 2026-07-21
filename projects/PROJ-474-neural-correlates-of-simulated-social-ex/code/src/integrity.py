import os
import hashlib
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
import json

from src.config import load_config
from src.utils import get_logger

logger = get_logger(__name__)
config = load_config()

def get_state_path() -> Path:
    """Returns the path to the project state file."""
    return Path(config['paths']['state']) / 'projects' / 'PROJ-474-neural-correlates-social-ex.yaml'

def compute_file_hash(file_path: Path) -> str:
    """Computes SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_hashes() -> Dict[str, str]:
    """Loads existing hashes from state file."""
    state_path = get_state_path()
    if not state_path.exists():
        return {}
    with open(state_path, 'r') as f:
        data = yaml.safe_load(f) or {}
    return data.get('artifact_hashes', {})

def save_hashes(hashes: Dict[str, str]) -> None:
    """Saves hashes to state file."""
    state_path = get_state_path()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    if state_path.exists():
        with open(state_path, 'r') as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {}
    
    data['artifact_hashes'] = hashes
    with open(state_path, 'w') as f:
        yaml.dump(data, f)

def update_hashes():
    """
    Scans data directories and updates hashes in state file.
    Called after artifact creation.
    """
    processed_dir = Path(config['paths']['processed'])
    results_dir = Path(config['paths']['results'])
    raw_dir = Path(config['paths']['raw'])
    
    current_hashes = load_hashes()
    
    def scan_dir(directory: Path, prefix: str):
        if not directory.exists():
            return
        for file in directory.rglob('*'):
            if file.is_file():
                rel_path = file.relative_to(directory.parent)
                key = f"{prefix}/{rel_path}"
                current_hashes[str(key)] = compute_file_hash(file)
    
    scan_dir(processed_dir, "processed")
    scan_dir(results_dir, "results")
    scan_dir(raw_dir, "raw")
    
    save_hashes(current_hashes)
    logger.info("Updated artifact hashes in state file.")

def main():
    update_hashes()

if __name__ == '__main__':
    main()
