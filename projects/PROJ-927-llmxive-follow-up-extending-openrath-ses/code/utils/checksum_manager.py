"""
Checksum Manager for Data Hygiene.

Provides utilities to calculate SHA256 hashes for files and manage
artifact hashes in the project's YAML state file.
"""
import hashlib
import os
from pathlib import Path
from typing import Dict, Optional, List

# Import config utilities to ensure paths and state handling consistency
from config import ensure_directories, load_state, save_state


def calculate_sha256(file_path: str) -> str:
    """
    Calculate the SHA256 hash of a file.

    Args:
        file_path: Absolute or relative path to the file.

    Returns:
        Hexadecimal string of the SHA256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If the path points to a directory.
    """
    sha256_hash = hashlib.sha256()
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if path.is_dir():
        raise IsADirectoryError(f"Path is a directory, not a file: {file_path}")

    with open(path, "rb") as f:
        # Read in chunks to handle large files efficiently
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)

    return sha256_hash.hexdigest()


def scan_directory_for_files(directory_path: str) -> List[str]:
    """
    Recursively scan a directory for all files.

    Args:
        directory_path: Path to the directory to scan.

    Returns:
        List of absolute paths to all files found.
    """
    files = []
    root = Path(directory_path)
    if not root.exists() or not root.is_dir():
        return files

    for file_path in root.rglob("*"):
        if file_path.is_file():
            files.append(str(file_path))

    return sorted(files)


def update_artifact_hashes(
    target_dir: Optional[str] = None,
    state_file: Optional[str] = None
) -> Dict[str, str]:
    """
    Calculate SHA256 hashes for all files in a target directory
    and update the project's YAML state file.

    Args:
        target_dir: Directory to scan for artifacts. Defaults to 'data/'.
        state_file: Path to the state YAML file. Defaults to
                    'state/projects/PROJ-927-llmxive-follow-up-extending-openrath-ses.yaml'.

    Returns:
        Dictionary mapping relative file paths to their SHA256 hashes.

    Raises:
        FileNotFoundError: If the target directory or state file does not exist.
        ValueError: If the state file is not a valid YAML (handled by save_state/load_state).
    """
    # Defaults based on project structure
    if target_dir is None:
        target_dir = "data"
    if state_file is None:
        state_file = "state/projects/PROJ-927-llmxive-follow-up-extending-openrath-ses.yaml"

    target_path = Path(target_dir)
    state_path = Path(state_file)

    if not target_path.exists():
        raise FileNotFoundError(f"Target directory does not exist: {target_dir}")

    if not state_path.exists():
        raise FileNotFoundError(f"State file does not exist: {state_file}")

    # Scan for files
    file_paths = scan_directory_for_files(target_dir)

    if not file_paths:
        return {}

    # Calculate hashes
    artifact_hashes = {}
    for abs_path in file_paths:
        # Calculate relative path from project root or target dir?
        # Usually relative to project root for state tracking.
        # Assuming script runs from project root.
        rel_path = os.path.relpath(abs_path, start=".")
        try:
            file_hash = calculate_sha256(abs_path)
            artifact_hashes[rel_path] = file_hash
        except (FileNotFoundError, IsADirectoryError) as e:
            # Log warning but continue with other files
            # In a real implementation, we might use logging.warning()
            pass

    # Load state, update, and save
    state = load_state(state_file)

    # Ensure 'artifact_hashes' key exists
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}

    # Update the map
    state["artifact_hashes"].update(artifact_hashes)

    # Save back to YAML
    save_state(state_file, state)

    return artifact_hashes
