"""
Utility functions for checksums and file operations.
"""
import hashlib
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import yaml
from datetime import datetime, timezone

from config import get_path_env_override

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    """Verify a file's checksum against an expected value."""
    actual_checksum = compute_sha256(file_path)
    return actual_checksum == expected_checksum

def scan_directory_for_checksums(directory: Path) -> Dict[str, str]:
    """Scan a directory and return checksums for all files."""
    checksums = {}
    for file_path in directory.rglob('*'):
        if file_path.is_file():
            checksums[str(file_path)] = compute_sha256(file_path)
    return checksums

def update_state_file_with_checksums(state_file_path: Path, checksums: Dict[str, str], artifact_name: Optional[str] = None):
    """Update the project state YAML file with new checksums."""
    state_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    if state_file_path.exists():
        with open(state_file_path, 'r') as f:
            state = yaml.safe_load(f) or {}
    else:
        state = {}
    
    if 'artifact_hashes' not in state:
        state['artifact_hashes'] = {}
    
    for key, value in checksums.items():
        # If artifact_name is provided, nest under it, else direct update
        if artifact_name:
            state['artifact_hashes'][artifact_name] = value
        else:
            state['artifact_hashes'][key] = value
    
    state['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    with open(state_file_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)

def main():
    """Entry point for utils."""
    logging.info("Utils module loaded.")

if __name__ == '__main__':
    main()