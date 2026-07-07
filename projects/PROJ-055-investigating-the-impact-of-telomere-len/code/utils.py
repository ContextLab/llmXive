"""
Utility functions for file validation and state management.
Provides SHA256 checksum generation and state file updates.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml


def generate_checksum(file_path: str) -> str:
    """
    Calculate the SHA256 checksum of a file.

    Args:
        file_path: Path to the file to checksum.

    Returns:
        Hexadecimal string of the SHA256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")


def validate_file_exists(file_path: str) -> bool:
    """
    Check if a file exists at the given path.

    Args:
        file_path: Path to the file.

    Returns:
        True if the file exists, False otherwise.
    """
    return Path(file_path).exists()


def update_state_file(hash_map: Dict[str, str], state_path: Optional[str] = None) -> None:
    """
    Update the project state file with a map of artifact paths to their checksums.

    This function loads the existing state file (if it exists), updates the
    'artifact_hashes' section with the provided hash_map, and writes the
    updated state back to disk.

    Args:
        hash_map: A dictionary mapping relative artifact paths to their SHA256 checksums.
        state_path: Optional path to the state file. Defaults to
                    'state/projects/PROJ-055-investigating-the-impact-of-telomere-len.yaml'.

    Raises:
        FileNotFoundError: If the state file does not exist and needs to be created
                           but the parent directory does not exist.
        yaml.YAMLError: If the state file contains invalid YAML.
        json.JSONDecodeError: If the state file contains invalid JSON (fallback).
    """
    if state_path is None:
        state_path = "state/projects/PROJ-055-investigating-the-impact-of-telomere-len.yaml"

    state_file = Path(state_path)
    state_dir = state_file.parent

    # Ensure directory exists
    if not state_dir.exists():
        state_dir.mkdir(parents=True, exist_ok=True)

    # Load existing state or initialize new
    current_state = {"artifact_hashes": {}, "last_updated": None}

    if state_file.exists():
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                content = yaml.safe_load(f)
                if content and isinstance(content, dict):
                    current_state = content
                    # Ensure artifact_hashes exists
                    if "artifact_hashes" not in current_state:
                        current_state["artifact_hashes"] = {}
        except yaml.YAMLError:
            # Fallback if YAML is corrupted, start fresh
            pass

    # Update hashes
    current_state["artifact_hashes"].update(hash_map)

    # Update timestamp
    import datetime
    current_state["last_updated"] = datetime.datetime.now().isoformat()

    # Write back
    with open(state_file, "w", encoding="utf-8") as f:
        yaml.dump(current_state, f, default_flow_style=False, sort_keys=False)