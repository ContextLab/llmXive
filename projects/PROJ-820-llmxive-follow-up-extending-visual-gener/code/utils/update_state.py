"""
Update state files with SHA-256 hashes of artifacts.

This module scans directories and calculates SHA-256 hashes for all files,
then updates the project state YAML file with these hashes.
"""

import os
import sys
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

def calculate_sha256(file_path: Path) -> str:
    """
    Calculate SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file
    
    Returns:
        Hexadecimal string of the SHA-256 hash
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def scan_directory(directory: Path, extensions: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Scan a directory and calculate hashes for all files.
    
    Args:
        directory: Path to the directory to scan
        extensions: Optional list of file extensions to include (e.g., ['.py', '.json'])
                   If None, include all files
    
    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes
    """
    hashes = {}
    
    if not directory.exists():
        print(f"Warning: Directory {directory} does not exist, skipping.")
        return hashes
    
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            # Check extension filter
            if extensions is not None:
                if file_path.suffix not in extensions:
                    continue
            
            # Calculate relative path
            rel_path = file_path.relative_to(directory)
            hashes[str(rel_path)] = calculate_sha256(file_path)
    
    return hashes

def update_state_file(state_path: Path, hashes: Dict[str, Dict[str, str]]) -> None:
    """
    Update the state YAML/JSON file with new hashes.
    
    Args:
        state_path: Path to the state file
        hashes: Dictionary mapping directory names to their file hashes
    """
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing state or create new
    if state_path.exists():
        with open(state_path, 'r') as f:
            state = json.load(f)
    else:
        state = {"artifacts": {}}
    
    # Update with new hashes
    for dir_name, dir_hashes in hashes.items():
        state["artifacts"][dir_name] = dir_hashes
    
    # Add timestamp
    import datetime
    state["last_updated"] = datetime.datetime.now().isoformat()
    
    # Write back
    with open(state_path, 'w') as f:
        json.dump(state, f, indent=2)
    
    print(f"Updated state file: {state_path}")

def main() -> None:
    """
    Main entry point for state update.
    
    Scans key directories and updates the state file.
    """
    # Define directories to scan
    directories = [
        Path("code"),
        Path("data/derived"),
        Path("data/processed"),
        Path("specs/001-llmxive-followup")
    ]
    
    # Define state file path
    state_path = Path("state/projects/llmxive-followup.json")
    
    # Scan directories and collect hashes
    all_hashes = {}
    for directory in directories:
        if directory.exists():
            dir_name = directory.name
            hashes = scan_directory(directory)
            if hashes:
                all_hashes[dir_name] = hashes
    
    if all_hashes:
        update_state_file(state_path, all_hashes)
    else:
        print("No artifacts found to hash.")

if __name__ == "__main__":
    main()
