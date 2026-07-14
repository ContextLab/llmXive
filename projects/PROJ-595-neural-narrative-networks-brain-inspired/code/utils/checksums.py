"""
Checksum utilities for data integrity verification.

Provides SHA-256 hashing and state file management for the pipeline.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

from config import get_config
from utils.logging_config import get_logger, error, info

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_directory_checksums(dir_path: Path) -> Dict[str, str]:
    """Compute checksums for all files in a directory (non-recursive)."""
    checksums = {}
    for file_path in sorted(dir_path.iterdir()):
        if file_path.is_file():
            checksums[file_path.name] = compute_sha256(file_path)
    return checksums

def load_state_file(state_path: Path) -> Dict[str, Any]:
    """Load existing state file or return empty dict if not found."""
    if not state_path.exists():
        return {}
    
    try:
        with open(state_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        error(f"Failed to load state file {state_path}: {e}")
        return {}

def update_state_file(
    current_state: Dict[str, Any],
    new_checksums: Dict[str, Dict[str, str]],
    save: bool = False,
    state_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Update state with new checksums and optionally save to disk.
    
    Args:
        current_state: Existing state dictionary
        new_checksums: New checksums to merge (dir_path -> {filename: hash})
        save: If True, write to disk
        state_path: Path to state file (required if save=True)
    
    Returns:
        Updated state dictionary
    """
    updated_state = current_state.copy()
    
    # Merge new checksums
    for dir_path, file_checksums in new_checksums.items():
        updated_state[dir_path] = {
            "checksums": file_checksums,
            "updated_at": str(Path(dir_path).stat().st_mtime) if Path(dir_path).exists() else None
        }
    
    if save:
        if not state_path:
            raise ValueError("state_path required when save=True")
        
        state_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(state_path, "w") as f:
                json.dump(updated_state, f, indent=2)
            info(f"State file saved to {state_path}")
        except IOError as e:
            error(f"Failed to write state file {state_path}: {e}")
            raise
    
    return updated_state

def verify_file_integrity(file_path: Path, expected_hash: str) -> bool:
    """Verify a file's integrity against an expected hash."""
    if not file_path.exists():
        return False
    
    actual_hash = compute_sha256(file_path)
    return actual_hash == expected_hash

def batch_update_state_files(
    state_files: List[Path],
    new_checksums: Dict[str, Dict[str, str]]
) -> Dict[str, bool]:
    """
    Update multiple state files with new checksums.
    
    Returns a dict mapping state file path to success status.
    """
    results = {}
    
    for state_path in state_files:
        try:
            current = load_state_file(state_path)
            updated = update_state_file(current, new_checksums, save=True, state_path=state_path)
            results[str(state_path)] = True
        except Exception as e:
            error(f"Failed to update {state_path}: {e}")
            results[str(state_path)] = False
    
    return results
