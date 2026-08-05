"""
State management utilities for tracking artifact checksums and project state.
Implements FR-012: State file updates with SHA-256 hashes.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml


def calculate_sha256(file_path: Path) -> str:
    """
    Calculate SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash
        
    Returns:
        str: Hexadecimal SHA-256 hash string
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def calculate_string_sha256(content: str) -> str:
    """
    Calculate SHA-256 hash of a string.
    
    Args:
        content: String content to hash
        
    Returns:
        str: Hexadecimal SHA-256 hash string
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def load_state(state_file: Path) -> Dict[str, Any]:
    """
    Load state file from YAML.
    
    Args:
        state_file: Path to the state YAML file
        
    Returns:
        Dictionary containing state data
    """
    if not state_file.exists():
        return {
            "project_id": "PROJ-298-statistical-analysis-of-publicly-availab",
            "artifacts": {},
            "last_updated": None
        }
    
    with open(state_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def save_state(state: Dict[str, Any], state_file: Path) -> None:
    """
    Save state dictionary to YAML file.
    
    Args:
        state: State dictionary to save
        state_file: Path to the state YAML file
    """
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, 'w', encoding='utf-8') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)


def update_artifact_checksums(
    state: Dict[str, Any],
    artifact_path: str,
    checksum: str
) -> Dict[str, Any]:
    """
    Update or add checksum for an artifact in the state.
    
    Args:
        state: Current state dictionary
        artifact_path: Relative path to the artifact
        checksum: SHA-256 checksum of the artifact
        
    Returns:
        Updated state dictionary
    """
    if "artifacts" not in state:
        state["artifacts"] = {}
    
    state["artifacts"][artifact_path] = {
        "sha256": checksum,
        "updated": True
    }
    
    return state


def initialize_state_file(state_file: Path, project_id: str = "PROJ-298-statistical-analysis-of-publicly-availab") -> Dict[str, Any]:
    """
    Initialize a new state file with project metadata.
    
    Args:
        state_file: Path to the state YAML file to create
        project_id: Project identifier
        
    Returns:
        Initialized state dictionary
    """
    state = {
        "project_id": project_id,
        "artifacts": {},
        "last_updated": None
    }
    
    state_file.parent.mkdir(parents=True, exist_ok=True)
    save_state(state, state_file)
    
    return state


def main():
    """
    Demo/main entry point for state manager utilities.
    """
    print("State Manager Utilities")
    print("-" * 40)
    
    # Test string hashing
    test_str = "Hello, World!"
    hash_val = calculate_string_sha256(test_str)
    print(f"SHA-256 of '{test_str}': {hash_val}")
    
    # Test file hashing (if a test file exists)
    test_file = Path("test_hash.txt")
    if test_file.exists():
        file_hash = calculate_sha256(test_file)
        print(f"SHA-256 of '{test_file}': {file_hash}")
    else:
        print(f"No test file found at {test_file}")
    
    print("\nUtilities available:")
    print("  - calculate_sha256(file_path)")
    print("  - calculate_string_sha256(content)")
    print("  - load_state(state_file)")
    print("  - save_state(state, state_file)")
    print("  - update_artifact_checksums(state, path, checksum)")
    print("  - initialize_state_file(state_file, project_id)")


if __name__ == "__main__":
    main()
