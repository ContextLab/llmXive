"""
Checksum verification and state file management for raw data.

This module provides functions to calculate SHA256 hashes of files,
maintain a state file tracking registered files and their hashes,
and verify data integrity by comparing current hashes against stored values.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Optional, Tuple, List

# Constants
STATE_FILE_NAME = ".data_state.json"
CHUNK_SIZE = 8192  # 8KB chunks for reading large files


def get_state_file_path(root_dir: Optional[Path] = None) -> Path:
    """
    Get the path to the state file.

    Args:
        root_dir: The root directory to store the state file. Defaults to the project root.

    Returns:
        Path to the state file.
    """
    if root_dir is None:
        # Default to project root (assumed to be the parent of 'src')
        root_dir = Path(__file__).resolve().parent.parent.parent
    return root_dir / STATE_FILE_NAME


def calculate_sha256(file_path: Path) -> str:
    """
    Calculate the SHA256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If the path points to a directory instead of a file.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if file_path.is_dir():
        raise IsADirectoryError(f"Path is a directory, not a file: {file_path}")

    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()


def load_state(state_file: Optional[Path] = None) -> Dict:
    """
    Load the state file containing registered file hashes.

    Args:
        state_file: Path to the state file. If None, uses the default location.

    Returns:
        Dictionary containing file paths as keys and their SHA256 hashes as values.
        Returns an empty dict if the file does not exist.
    """
    if state_file is None:
        state_file = get_state_file_path()
    
    if not state_file.exists():
        return {}
    
    with open(state_file, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state: Dict, state_file: Optional[Path] = None) -> None:
    """
    Save the state dictionary to the state file.

    Args:
        state: Dictionary of file paths and their SHA256 hashes.
        state_file: Path to the state file. If None, uses the default location.
    """
    if state_file is None:
        state_file = get_state_file_path()
    
    # Ensure parent directory exists
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)


def verify_file(file_path: Path, state_file: Optional[Path] = None) -> Tuple[bool, str]:
    """
    Verify a single file's hash against the stored state.

    Args:
        file_path: Path to the file to verify.
        state_file: Path to the state file. If None, uses the default location.

    Returns:
        Tuple of (is_valid, message) where is_valid is True if the hash matches,
        and message provides details about the verification result.
    """
    if not file_path.exists():
        return False, f"File not found: {file_path}"
    
    state = load_state(state_file)
    file_str = str(file_path)
    
    if file_str not in state:
        return False, f"No registered hash for file: {file_path}"
    
    current_hash = calculate_sha256(file_path)
    stored_hash = state[file_str]
    
    if current_hash == stored_hash:
        return True, f"Hash verified for {file_path}"
    else:
        return False, f"Hash mismatch for {file_path}. Expected: {stored_hash}, Got: {current_hash}"


def register_file(file_path: Path, state_file: Optional[Path] = None) -> str:
    """
    Register a file's hash in the state file.

    Args:
        file_path: Path to the file to register.
        state_file: Path to the state file. If None, uses the default location.

    Returns:
        The calculated SHA256 hash of the file.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot register non-existent file: {file_path}")
    
    file_hash = calculate_sha256(file_path)
    
    state = load_state(state_file)
    state[str(file_path)] = file_hash
    save_state(state, state_file)
    
    return file_hash


def verify_all(state_file: Optional[Path] = None) -> List[Tuple[Path, bool, str]]:
    """
    Verify all registered files against their stored hashes.

    Args:
        state_file: Path to the state file. If None, uses the default location.

    Returns:
        List of tuples (file_path, is_valid, message) for each registered file.
    """
    state = load_state(state_file)
    results = []
    
    for file_str, stored_hash in state.items():
        file_path = Path(file_str)
        
        if not file_path.exists():
            results.append((file_path, False, f"File not found: {file_path}"))
            continue
        
        try:
            current_hash = calculate_sha256(file_path)
            if current_hash == stored_hash:
                results.append((file_path, True, f"Hash verified for {file_path}"))
            else:
                results.append((file_path, False, f"Hash mismatch for {file_path}. Expected: {stored_hash}, Got: {current_hash}"))
        except Exception as e:
            results.append((file_path, False, f"Error verifying {file_path}: {str(e)}"))
    
    return results


def check_and_register_missing_files(
    data_dirs: List[Path],
    state_file: Optional[Path] = None,
    recursive: bool = True
) -> List[Tuple[Path, str]]:
    """
    Check for files in the given directories that are not registered in the state file
    and register them.

    Args:
        data_dirs: List of directories to scan for files.
        state_file: Path to the state file. If None, uses the default location.
        recursive: If True, scan subdirectories recursively.

    Returns:
        List of tuples (file_path, hash) for newly registered files.
    """
    state = load_state(state_file)
    newly_registered = []
    
    for data_dir in data_dirs:
        if not data_dir.exists():
            continue
        
        if recursive:
            files = list(data_dir.rglob("*"))
        else:
            files = list(data_dir.glob("*"))
        
        for file_path in files:
            if file_path.is_file():
                file_str = str(file_path)
                if file_str not in state:
                    try:
                        file_hash = register_file(file_path, state_file)
                        newly_registered.append((file_path, file_hash))
                    except Exception:
                        # Skip files that can't be read
                        pass
    
    return newly_registered
