"""
Utility functions for SHA-256 checksum computation and tracking.

This module provides functions to compute checksums for data files
and manage artifact hash tracking as required by Constitution III.
"""
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Optional
import yaml


def compute_sha256(file_path: Path, chunk_size: int = 8192) -> str:
    """
    Compute SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash
        chunk_size: Size of chunks to read (default 8KB)
    
    Returns:
        Hexadecimal SHA-256 hash string
    
    Raises:
        FileNotFoundError: If the file does not exist
        PermissionError: If the file cannot be read
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def scan_directory_for_checksums(
    directory: Path,
    extensions: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Scan a directory recursively and compute SHA-256 checksums for all files.
    
    Args:
        directory: Path to the directory to scan
        extensions: Optional list of file extensions to include (e.g., ['.csv', '.json'])
                   If None, all files are included
    
    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes
    
    Raises:
        FileNotFoundError: If the directory does not exist
    """
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")
    
    checksums = {}
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            if extensions is None or any(file_path.suffix == ext for ext in extensions):
                rel_path = file_path.relative_to(directory)
                checksums[str(rel_path)] = compute_sha256(file_path)
    
    return checksums


def load_artifact_hashes(state_file: Path) -> Dict:
    """
    Load existing artifact hashes from the state YAML file.
    
    Args:
        state_file: Path to the state YAML file
    
    Returns:
        Dictionary containing the state data, or empty dict if file doesn't exist
    """
    if not state_file.exists():
        return {
            "project_id": "PROJ-035-exploring-the-correlation-between-crysta",
            "artifact_hashes": {}
        }
    
    with open(state_file, "r") as f:
        return yaml.safe_load(f) or {}


def save_artifact_hashes(state_file: Path, data: Dict) -> None:
    """
    Save artifact hashes to the state YAML file.
    
    Args:
        state_file: Path to the state YAML file
        data: Dictionary containing the state data to save
    """
    # Ensure parent directory exists
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(state_file, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def update_checksums_for_raw_data(
    raw_data_dir: Path,
    state_file: Path
) -> Dict:
    """
    Update the artifact hashes for all files in the raw data directory.
    
    This function scans the raw data directory, computes SHA-256 checksums,
    and updates the project state file as required by Constitution III.
    
    Args:
        raw_data_dir: Path to the raw data directory
        state_file: Path to the state YAML file for storing hashes
    
    Returns:
        Updated state dictionary with new checksums
    """
    # Load existing state
    state_data = load_artifact_hashes(state_file)
    
    # Ensure project_id is set
    if "project_id" not in state_data:
        state_data["project_id"] = "PROJ-035-exploring-the-correlation-between-crysta"
    
    # Ensure artifact_hashes key exists
    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}
    
    # Compute checksums for raw data files
    raw_data_checksums = scan_directory_for_checksums(raw_data_dir)
    
    # Store under 'raw_data' key in artifact_hashes
    state_data["artifact_hashes"]["raw_data"] = raw_data_checksums
    
    # Save updated state
    save_artifact_hashes(state_file, state_data)
    
    return state_data
