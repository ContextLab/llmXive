"""
Utility functions for checksum generation and state management.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

def generate_checksum(file_path: str | Path) -> str:
    """
    Generate SHA256 checksum for a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hex digest string of the SHA256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_state_file(hash_map: Dict[str, str]) -> None:
    """
    Update the project state YAML file with new artifact hashes.
    
    Args:
        hash_map: Dictionary mapping filenames to their SHA256 hashes.
    """
    state_path = Path("state/projects/PROJ-055-investigating-the-impact-of-telomere-len.yaml")
    
    # Ensure directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing state or create new
    if state_path.exists():
        with open(state_path, 'r') as f:
            try:
                state_data = yaml.safe_load(f) or {}
            except yaml.YAMLError:
                state_data = {}
    else:
        state_data = {
            "artifact_hashes": {},
            "last_updated": None
        }
    
    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}
    
    # Update hashes
    for filename, hash_val in hash_map.items():
        state_data["artifact_hashes"][filename] = hash_val
    
    # Update timestamp
    import datetime
    state_data["last_updated"] = datetime.datetime.now().isoformat()
    
    # Write back
    with open(state_path, 'w') as f:
        yaml.safe_dump(state_data, f, default_flow_style=False)

def validate_file_exists(file_path: str | Path) -> bool:
    """Check if a file exists."""
    return Path(file_path).exists()
