"""
Module: versioning

Purpose:
    Manages versioning of data artifacts by computing SHA-256 hashes
    and writing them to state files for reproducibility.

Functions:
    - compute_sha256: Computes SHA-256 hash of a file.
    - hash_artifact: Hashes a specific artifact.
    - hash_directory: Hashes all files in a directory.
    - verify_artifact: Verifies an artifact against a hash.
    - write_version_manifest: Writes a version manifest.
    - write_project_state_yaml: Writes project state to YAML.
    - main: Entry point for the script.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

from utils.config import get_project_root, get_path, ensure_dir, get_config

def compute_sha256(file_path: Path) -> str:
    """
    Computes the SHA-256 hash of a file.

    Args:
        file_path (Path): Path to the file.

    Returns:
        str: Hex digest of the hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def hash_artifact(file_path: Path) -> str:
    """
    Hashes a specific artifact.

    Args:
        file_path (Path): Path to the file.

    Returns:
        str: Hash string.
    """
    return compute_sha256(file_path)

def hash_directory(directory: Path) -> Dict[str, str]:
    """
    Hashes all files in a directory.

    Args:
        directory (Path): Path to the directory.

    Returns:
        Dict[str, str]: Mapping of filenames to hashes.
    """
    hashes = {}
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            hashes[str(file_path.relative_to(directory))] = compute_sha256(file_path)
    return hashes

def verify_artifact(file_path: Path, expected_hash: str) -> bool:
    """
    Verifies an artifact against an expected hash.

    Args:
        file_path (Path): Path to the file.
        expected_hash (str): Expected hash.

    Returns:
        bool: True if valid.
    """
    actual_hash = compute_sha256(file_path)
    return actual_hash == expected_hash

def write_version_manifest(artifacts: Dict[str, str], output_path: Path):
    """
    Writes a version manifest to a JSON file.

    Args:
        artifacts (Dict[str, str]): Mapping of names to hashes.
        output_path (Path): Output path.
    """
    ensure_dir(output_path.parent)
    with open(output_path, 'w') as f:
        json.dump(artifacts, f, indent=2)

def write_project_state_yaml(state: Dict[str, Any], output_path: Path):
    """
    Writes project state to a YAML file.

    Args:
        state (Dict[str, Any]): State dictionary.
        output_path (Path): Output path.
    """
    import yaml
    ensure_dir(output_path.parent)
    with open(output_path, 'w') as f:
        yaml.dump(state, f)

def main():
    """
    Main entry point for the versioning script.
    """
    project_root = get_project_root()
    # Example usage
    file_path = project_root / "data" / "processed" / "annotated_videokr.csv"
    if file_path.exists():
        h = hash_artifact(file_path)
        print(f"Hash: {h}")
    else:
        print("File not found.")

if __name__ == "__main__":
    main()