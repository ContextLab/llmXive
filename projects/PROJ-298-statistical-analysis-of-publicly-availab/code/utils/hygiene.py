"""
Hygiene module for SHA-256 hashing and state file updates per FR-012.

This module provides utilities to:
1. Calculate SHA-256 hashes of files and strings.
2. Load and save the project state file (YAML).
3. Update artifact checksums in the state file to ensure data integrity tracking.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

import yaml

# Default path for the state file relative to project root
DEFAULT_STATE_PATH = "state/projects/PROJ-298-statistical-analysis-of-publicly-availab.yaml"


def calculate_sha256(file_path: str) -> str:
    """
    Calculate the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.

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
            # Read in chunks to handle large files without loading entirely into memory
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")


def calculate_string_sha256(data: str) -> str:
    """
    Calculate the SHA-256 hash of a string.

    Args:
        data: String data to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def load_state(state_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the state file from disk.

    Args:
        state_path: Optional override for the state file path. Defaults to DEFAULT_STATE_PATH.

    Returns:
        Dictionary containing the state data. Returns an empty dict if file doesn't exist.
    """
    path = Path(state_path or DEFAULT_STATE_PATH)
    
    if not path.exists():
        return {}
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in state file {path}: {e}")


def save_state(state: Dict[str, Any], state_path: Optional[str] = None) -> None:
    """
    Save the state dictionary to disk.

    Args:
        state: The state dictionary to save.
        state_path: Optional override for the state file path.
    """
    path = Path(state_path or DEFAULT_STATE_PATH)
    
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(state, f, default_flow_style=False, sort_keys=False)


def update_artifact_checksums(
    artifact_paths: List[str],
    state_path: Optional[str] = None,
    artifact_type: str = "processed"
) -> Dict[str, Any]:
    """
    Calculate SHA-256 checksums for a list of artifact paths and update the state file.

    This function fulfills FR-012 by ensuring all processed artifacts have their
    checksums recorded in the central state file.

    Args:
        artifact_paths: List of relative or absolute paths to artifacts.
        state_path: Optional override for the state file path.
        artifact_type: Category of artifacts (e.g., 'processed', 'raw', 'visuals').
                       Defaults to 'processed'.

    Returns:
        The updated state dictionary.
    
    Raises:
        FileNotFoundError: If any of the artifact paths do not exist.
    """
    state = load_state(state_path)
    
    # Initialize structure if missing
    if "artifacts" not in state:
        state["artifacts"] = {}
    
    if artifact_type not in state["artifacts"]:
        state["artifacts"][artifact_type] = {}
    
    current_checksums = {}
    
    for path_str in artifact_paths:
        p = Path(path_str)
        if not p.exists():
            raise FileNotFoundError(f"Artifact not found for checksum update: {path_str}")
        
        # Use relative path from project root if possible, otherwise absolute
        try:
            rel_path = p.resolve().relative_to(Path.cwd())
            key = str(rel_path)
        except ValueError:
            key = str(p.resolve())
        
        checksum = calculate_sha256(str(p))
        current_checksums[key] = checksum
        
        # Update state
        state["artifacts"][artifact_type][key] = {
            "checksum": checksum,
            "last_updated": str(p.stat().st_mtime)
        }
    
    # Save updated state
    save_state(state, state_path)
    
    return state


def initialize_state_file(state_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Initialize a new state file with default structure if it doesn't exist.

    Args:
        state_path: Optional override for the state file path.

    Returns:
        The initialized state dictionary.
    """
    path = Path(state_path or DEFAULT_STATE_PATH)
    
    if path.exists():
        return load_state(state_path)
    
    state = {
        "project_id": "PROJ-298-statistical-analysis-of-publicly-availab",
        "version": "1.0.0",
        "initialized_at": str(Path.cwd().joinpath("now").stat().st_mtime) if False else "init", # Placeholder for time
        "artifacts": {
            "raw": {},
            "processed": {},
            "visuals": {},
            "taxonomies": {}
        },
        "metadata": {
            "python_version": "3.11",
            "dependencies": []
        }
    }
    
    # Clean up placeholder time logic for actual use
    import time
    state["initialized_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    
    save_state(state, state_path)
    return state


def main() -> None:
    """
    CLI entry point for hygiene utilities.
    Demonstrates usage of hashing and state management.
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m utils.hygiene <command> [args]")
        print("Commands:")
        print("  hash <file_path>          : Calculate SHA-256 of a file")
        print("  init_state                : Initialize the state file")
        print("  update_checksums <path1> [path2...] : Update checksums for artifacts")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "hash":
        if len(sys.argv) < 3:
            print("Error: File path required for 'hash' command.")
            sys.exit(1)
        file_path = sys.argv[2]
        try:
            h = calculate_sha256(file_path)
            print(f"SHA-256: {h}")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    elif command == "init_state":
        try:
            state = initialize_state_file()
            print(f"State file initialized at {DEFAULT_STATE_PATH}")
            print(json.dumps(state, indent=2))
        except Exception as e:
            print(f"Error initializing state: {e}")
            sys.exit(1)
    
    elif command == "update_checksums":
        if len(sys.argv) < 3:
            print("Error: At least one artifact path required.")
            sys.exit(1)
        paths = sys.argv[2:]
        try:
            new_state = update_artifact_checksums(paths)
            print(f"State updated. Checksums recorded for {len(paths)} artifacts.")
            print(json.dumps(new_state["artifacts"], indent=2))
        except Exception as e:
            print(f"Error updating checksums: {e}")
            sys.exit(1)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()