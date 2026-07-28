"""
src/data/checksum.py

Implements raw data hash verification and state file management.
This module ensures data integrity by calculating SHA-256 checksums
and maintaining a state file that tracks registered files and their hashes.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Optional, Tuple, List

# Configuration
STATE_FILE_NAME = "data_state.json"
CHUNK_SIZE = 8192  # Read files in 8KB chunks for memory efficiency


def get_state_file_path(project_root: Optional[Path] = None) -> Path:
    """
    Returns the path to the state file.
    
    Args:
        project_root: Optional base path. Defaults to current working directory.
        
    Returns:
        Path to the data state JSON file.
    """
    if project_root is None:
        project_root = Path.cwd()
    return project_root / "data" / STATE_FILE_NAME


def calculate_sha256(file_path: Path) -> str:
    """
    Calculates the SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If the path is a directory.
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


def load_state(project_root: Optional[Path] = None) -> Dict:
    """
    Loads the current state from the JSON file.
    
    Args:
        project_root: Optional base path. Defaults to current working directory.
        
    Returns:
        Dictionary containing the state data. Returns empty dict if file missing.
    """
    state_path = get_state_file_path(project_root)
    if not state_path.exists():
        return {"files": {}, "metadata": {"created": None, "last_updated": None}}
    
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        raise RuntimeError(f"Failed to load state file {state_path}: {e}")


def save_state(state: Dict, project_root: Optional[Path] = None) -> None:
    """
    Saves the state dictionary to the JSON file.
    
    Args:
        state: Dictionary to save.
        project_root: Optional base path. Defaults to current working directory.
    """
    import datetime
    state_path = get_state_file_path(project_root)
    
    # Ensure directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Update metadata
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    state["metadata"]["last_updated"] = now
    if state["metadata"].get("created") is None:
        state["metadata"]["created"] = now
        
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def verify_file(file_path: Path, expected_hash: str, project_root: Optional[Path] = None) -> Tuple[bool, str]:
    """
    Verifies a file's hash against an expected value.
    
    Args:
        file_path: Path to the file to verify.
        expected_hash: The expected SHA-256 hash.
        project_root: Optional base path.
        
    Returns:
        Tuple of (is_valid, message).
    """
    if not file_path.exists():
        return False, f"File missing: {file_path}"
    
    try:
        actual_hash = calculate_sha256(file_path)
    except Exception as e:
        return False, f"Error calculating hash: {e}"
    
    if actual_hash == expected_hash:
        return True, "Hash verified successfully"
    else:
        return False, f"Hash mismatch. Expected: {expected_hash}, Got: {actual_hash}"


def register_file(file_path: Path, project_root: Optional[Path] = None) -> str:
    """
    Calculates hash for a file and registers it in the state file.
    
    Args:
        file_path: Path to the file to register.
        project_root: Optional base path.
        
    Returns:
        The calculated hash.
        
    Raises:
        FileNotFoundError: If file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot register missing file: {file_path}")
    
    file_hash = calculate_sha256(file_path)
    state = load_state(project_root)
    
    # Store relative path from project root for portability
    if project_root is None:
        project_root = Path.cwd()
    relative_path = str(file_path.relative_to(project_root))
    
    state["files"][relative_path] = {
        "hash": file_hash,
        "registered_at": file_path.stat().st_mtime,
        "size_bytes": file_path.stat().st_size
    }
    
    save_state(state, project_root)
    return file_hash


def verify_all(project_root: Optional[Path] = None) -> Dict[str, bool]:
    """
    Verifies all registered files against their stored hashes.
    
    Args:
        project_root: Optional base path.
        
    Returns:
        Dictionary mapping relative paths to verification status (True/False).
    """
    state = load_state(project_root)
    results = {}
    
    if project_root is None:
        project_root = Path.cwd()
        
    for relative_path, info in state.get("files", {}).items():
        full_path = project_root / relative_path
        is_valid, _ = verify_file(full_path, info["hash"])
        results[relative_path] = is_valid
        
    return results


def check_and_register_missing_files(file_paths: List[Path], project_root: Optional[Path] = None) -> List[Path]:
    """
    Checks a list of files against the state. Registers any that are missing
    from the state file.
    
    Args:
        file_paths: List of file paths to check.
        project_root: Optional base path.
        
    Returns:
        List of files that were newly registered.
    """
    state = load_state(project_root)
    newly_registered = []
    
    if project_root is None:
        project_root = Path.cwd()
        
    for file_path in file_paths:
        if not file_path.exists():
            continue
            
        relative_path = str(file_path.relative_to(project_root))
        
        if relative_path not in state.get("files", {}):
            register_file(file_path, project_root)
            newly_registered.append(file_path)
            
    return newly_registered
