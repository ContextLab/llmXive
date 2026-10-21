"""
Integrity checking module.
Manages file hashing and state tracking.
"""
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
    state_dir = Path(config.get('paths', {}).get('state', 'state'))
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / 'projects' / 'PROJ-474-neural-correlates-social-ex.yaml'

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

def update_hashes(file_list: Optional[List[str]] = None):
    """
    Scans data directories and updates hashes in state file.
    Called after artifact creation.
    
    Args:
        file_list: Optional list of specific files to hash.
                  If None, scans all data directories.
    """
    current_hashes = load_hashes()
    
    if file_list:
        # Hash specific files
        for file_path in file_list:
            fpath = Path(file_path)
            if fpath.exists() and fpath.is_file():
                file_hash = compute_file_hash(fpath)
                current_hashes[str(fpath)] = file_hash
                logger.info(f"Hashed {fpath}: {file_hash}")
    else:
        # Scan directories
        processed_dir = Path(config.get('paths', {}).get('processed', 'data/processed'))
        results_dir = Path(config.get('paths', {}).get('results', 'data/results'))
        raw_dir = Path(config.get('paths', {}).get('raw', 'data/raw'))
        
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
    """Entry point for integrity checking."""
    update_hashes()

if __name__ == '__main__':
    main()
