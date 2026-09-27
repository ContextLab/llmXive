"""
Checksum utilities for raw data hash verification and state file management.

This module provides functions to calculate SHA-256 hashes for files,
maintain a state file tracking known files and their checksums, and
verify data integrity across runs.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Optional, Tuple, List

# Default path for the state file relative to project root
DEFAULT_STATE_FILE = "data/raw/.checksum_state.json"


def get_state_file_path(project_root: Optional[Path] = None) -> Path:
    """
    Returns the path to the checksum state file.

    Args:
        project_root: Optional Path to the project root. If None, uses current directory.

    Returns:
        Path to the state file.
    """
    if project_root is None:
        project_root = Path.cwd()
    return project_root / DEFAULT_STATE_FILE


def calculate_sha256(file_path: Path, chunk_size: int = 8192) -> str:
    """
    Calculates the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.
        chunk_size: Size of chunks to read at a time.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If the path is a directory.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if file_path.is_dir():
        raise IsADirectoryError(f"Cannot hash a directory: {file_path}")

    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def load_state(state_file: Path) -> Dict[str, str]:
    """
    Loads the checksum state from a JSON file.

    Args:
        state_file: Path to the state file.

    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes.
        Returns an empty dict if the file does not exist.
    """
    if not state_file.exists():
        return {}

    with open(state_file, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def save_state(state_file: Path, state: Dict[str, str]) -> None:
    """
    Saves the checksum state to a JSON file.

    Args:
        state_file: Path to the state file.
        state: Dictionary mapping relative file paths to their SHA-256 hashes.
    """
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def verify_file(file_path: Path, state: Dict[str, str], project_root: Optional[Path] = None) -> Tuple[bool, Optional[str]]:
    """
    Verifies a single file against the stored state.

    Args:
        file_path: Path to the file to verify.
        state: Dictionary of known checksums.
        project_root: Optional Path to the project root.

    Returns:
        Tuple of (is_valid, error_message).
        is_valid is True if the file matches the stored checksum.
        error_message is None if valid, otherwise contains a description of the failure.
    """
    if project_root is None:
        project_root = Path.cwd()

    try:
        rel_path = str(file_path.relative_to(project_root))
    except ValueError:
        rel_path = str(file_path)

    if rel_path not in state:
        return False, "File not registered in state"

    stored_hash = state[rel_path]
    try:
        current_hash = calculate_sha256(file_path)
    except FileNotFoundError:
        return False, "File missing"
    except IsADirectoryError:
        return False, "Path is a directory"

    if current_hash != stored_hash:
        return False, f"Checksum mismatch: expected {stored_hash}, got {current_hash}"

    return True, None


def register_file(file_path: Path, state: Dict[str, str], project_root: Optional[Path] = None) -> None:
    """
    Registers a file's checksum in the state dictionary.

    Args:
        file_path: Path to the file to register.
        state: Dictionary to update.
        project_root: Optional Path to the project root.
    """
    if project_root is None:
        project_root = Path.cwd()

    try:
        rel_path = str(file_path.relative_to(project_root))
    except ValueError:
        rel_path = str(file_path)

    if file_path.is_dir():
        raise IsADirectoryError(f"Cannot register a directory: {file_path}")

    file_hash = calculate_sha256(file_path)
    state[rel_path] = file_hash


def verify_all(project_root: Optional[Path] = None) -> Tuple[bool, List[str]]:
    """
    Verifies all registered files against their stored checksums.

    Args:
        project_root: Optional Path to the project root.

    Returns:
        Tuple of (all_valid, list_of_error_messages).
    """
    if project_root is None:
        project_root = Path.cwd()

    state_file = get_state_file_path(project_root)
    state = load_state(state_file)

    errors = []
    all_valid = True

    for rel_path, _ in state.items():
        full_path = project_root / rel_path
        is_valid, error_msg = verify_file(full_path, state, project_root)
        if not is_valid:
            all_valid = False
            errors.append(f"{rel_path}: {error_msg}")

    return all_valid, errors


def check_and_register_missing_files(data_dir: Path, project_root: Optional[Path] = None) -> Tuple[int, List[str]]:
    """
    Scans a data directory for files not yet registered and adds them to the state.

    Args:
        data_dir: Path to the directory to scan.
        project_root: Optional Path to the project root.

    Returns:
        Tuple of (number_of_files_registered, list_of_registered_file_paths).
    """
    if project_root is None:
        project_root = Path.cwd()

    state_file = get_state_file_path(project_root)
    state = load_state(state_file)

    registered = []

    for file_path in data_dir.rglob("*"):
        if file_path.is_file() and not file_path.name.startswith("."):
            try:
                rel_path = str(file_path.relative_to(project_root))
            except ValueError:
                rel_path = str(file_path)

            if rel_path not in state:
                register_file(file_path, state, project_root)
                registered.append(rel_path)

    if registered:
        save_state(state_file, state)

    return len(registered), registered
