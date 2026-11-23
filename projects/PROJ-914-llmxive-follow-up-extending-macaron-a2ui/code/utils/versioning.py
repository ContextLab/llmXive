"""
Versioning utilities for the llmXive project.
Implements Constitution Principle V: Reproducibility via content hashing.
"""
import hashlib
import os
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

# Project root is the parent of the code/ directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATE_FILE_PATH = PROJECT_ROOT / "state" / "version_state.yaml"
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"


def compute_file_hash(file_path: Path) -> str:
    """
    Compute the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except (IOError, OSError) as e:
        raise RuntimeError(f"Failed to hash file {file_path}: {e}")


def compute_directory_hash(dir_path: Path, ignore_patterns: Optional[list] = None) -> str:
    """
    Compute a deterministic SHA-256 hash for a directory.
    Iterates files in sorted order to ensure determinism.

    Args:
        dir_path: Path to the directory to hash.
        ignore_patterns: List of filename patterns to ignore (e.g., ['.pyc', '__pycache__']).

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    if ignore_patterns is None:
        ignore_patterns = ['.pyc', '__pycache__', '.git']

    sha256_hash = hashlib.sha256()
    dir_path = Path(dir_path)

    if not dir_path.exists():
        # If directory doesn't exist, hash a specific string to indicate absence
        sha256_hash.update(b"DIR_NOT_FOUND")
        return sha256_hash.hexdigest()

    # Collect all files recursively
    files_to_hash = []
    for root, dirs, files in os.walk(dir_path):
        # Filter directories
        dirs[:] = [d for d in dirs if d not in ignore_patterns]

        for file in files:
            if any(file.endswith(p) for p in ignore_patterns):
                continue
            # Skip hidden files
            if file.startswith('.'):
                continue
            files_to_hash.append(Path(root) / file)

    # Sort files to ensure deterministic order
    files_to_hash.sort()

    # Update hash with relative path and content
    for file_path in files_to_hash:
        try:
            # Hash the relative path
            rel_path = file_path.relative_to(dir_path)
            sha256_hash.update(str(rel_path).encode('utf-8'))

            # Hash the content
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
        except (IOError, OSError, ValueError) as e:
            # Log warning but continue hashing other files
            # In a real system, we might want to abort or record this error
            pass

    return sha256_hash.hexdigest()


def compute_version_state() -> Dict[str, Any]:
    """
    Compute the version state for the project's code and data directories.

    Returns:
        Dictionary containing:
            - timestamp: ISO format timestamp
            - code_hash: SHA-256 hash of the code/ directory
            - data_hash: SHA-256 hash of the data/ directory
            - project_root: Absolute path to project root
    """
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "code_hash": compute_directory_hash(CODE_DIR),
        "data_hash": compute_directory_hash(DATA_DIR),
        "project_root": str(PROJECT_ROOT)
    }


def update_state_file() -> Dict[str, Any]:
    """
    Compute the current version state and write it to the state YAML file.

    Returns:
        The computed state dictionary.
    """
    state = compute_version_state()

    # Ensure state directory exists
    STATE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Write to YAML
    with open(STATE_FILE_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

    return state


def get_latest_state() -> Optional[Dict[str, Any]]:
    """
    Load the latest version state from the YAML file.

    Returns:
        Dictionary containing the state, or None if file doesn't exist.
    """
    if not STATE_FILE_PATH.exists():
        return None

    try:
        with open(STATE_FILE_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except (IOError, yaml.YAMLError) as e:
        raise RuntimeError(f"Failed to read state file {STATE_FILE_PATH}: {e}")


if __name__ == "__main__":
    # Example usage: compute and print version state
    print("Computing project version state...")
    state = update_state_file()
    print(f"Timestamp: {state['timestamp']}")
    print(f"Code Hash: {state['code_hash']}")
    print(f"Data Hash: {state['data_hash']}")
    print(f"State written to: {STATE_FILE_PATH}")