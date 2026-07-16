"""
Data Hygiene Module for llmXive Pipeline.

This module provides utilities for:
- SHA256 checksum generation and verification
- State management (locking, tracking file versions)
- Integrity validation of data artifacts
"""
import hashlib
import json
import os
import fcntl
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

from src.config import ensure_directories, get_data_path, get_processed_path


class StateLock:
    """
    Context manager for file locking to prevent concurrent writes to state files.
    Uses OS-level file locking (fcntl) for cross-process safety.
    """

    def __init__(self, state_path: Path):
        self.state_path = state_path
        self.lock_path = Path(str(state_path) + ".lock")
        self.lock_file = None

    def __enter__(self):
        ensure_directories(self.lock_path.parent)
        self.lock_file = open(self.lock_path, 'w')
        try:
            fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX)
        except (IOError, OSError) as e:
            raise RuntimeError(f"Failed to acquire lock on {self.lock_path}: {e}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.lock_file:
            fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
            self.lock_file.close()
            self.lock_file = None
            # Clean up lock file if empty or stale
            try:
                if self.lock_path.exists():
                    self.lock_path.unlink()
            except OSError:
                pass  # Ignore cleanup errors
        return False


def calculate_sha256(file_path: Path) -> str:
    """
    Calculate the SHA256 checksum of a file.

    Args:
        file_path: Path to the file to hash

    Returns:
        Hexadecimal string of the SHA256 hash

    Raises:
        FileNotFoundError: If the file does not exist
        IOError: If the file cannot be read
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Failed to read file {file_path} for hashing: {e}")


def load_checksums(state_path: Path) -> Dict[str, Any]:
    """
    Load checksums and state metadata from a JSON file.

    Args:
        state_path: Path to the state JSON file

    Returns:
        Dictionary containing checksums and metadata

    Note:
        If the file does not exist, returns an empty state structure.
    """
    if not state_path.exists():
        return {
            "version": "1.0",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "checksums": {}
        }

    try:
        with open(state_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        raise RuntimeError(f"Failed to load state file {state_path}: {e}")


def save_checksums(state_path: Path, state_data: Dict[str, Any]) -> None:
    """
    Save checksums and state metadata to a JSON file.

    Args:
        state_path: Path to the state JSON file
        state_data: Dictionary containing checksums and metadata

    Note:
        Updates the 'updated_at' timestamp before saving.
    """
    ensure_directories(state_path.parent)
    state_data["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(state_data, f, indent=2, sort_keys=True)


def update_checksum(
    state_path: Path,
    file_path: Path,
    relative_path: Optional[Path] = None
) -> None:
    """
    Calculate and store the SHA256 checksum for a file in the state file.

    Args:
        state_path: Path to the state JSON file
        file_path: Path to the file to checksum
        relative_path: Optional relative path to store instead of absolute

    Raises:
        FileNotFoundError: If the file does not exist
        RuntimeError: If state file operations fail
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot checksum non-existent file: {file_path}")

    with StateLock(state_path):
        state_data = load_checksums(state_path)
        checksum = calculate_sha256(file_path)

        key = str(relative_path) if relative_path else str(file_path)
        state_data["checksums"][key] = {
            "hash": checksum,
            "size_bytes": file_path.stat().st_size,
            "recorded_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        save_checksums(state_path, state_data)


def verify_checksum(
    state_path: Path,
    file_path: Path,
    relative_path: Optional[Path] = None
) -> bool:
    """
    Verify that a file's current checksum matches the stored checksum.

    Args:
        state_path: Path to the state JSON file
        file_path: Path to the file to verify
        relative_path: Optional relative path to look up in state

    Returns:
        True if checksums match, False otherwise

    Raises:
        FileNotFoundError: If the file or state file does not exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File to verify not found: {file_path}")

    key = str(relative_path) if relative_path else str(file_path)

    with StateLock(state_path):
        state_data = load_checksums(state_path)

    if key not in state_data.get("checksums", {}):
        raise KeyError(f"No checksum record found for: {key}")

    stored_hash = state_data["checksums"][key]["hash"]
    current_hash = calculate_sha256(file_path)

    return stored_hash == current_hash


def verify_all_checksums(state_path: Path) -> Dict[str, bool]:
    """
    Verify all files recorded in the state file.

    Args:
        state_path: Path to the state JSON file

    Returns:
        Dictionary mapping file keys to verification status (True/False)

    Note:
        Files that no longer exist are marked as False.
    """
    if not state_path.exists():
        return {}

    with StateLock(state_path):
        state_data = load_checksums(state_path)

    results = {}
    for key, record in state_data.get("checksums", {}).items():
        # Determine actual file path (handle relative keys)
        if not os.path.isabs(key):
            # Try to resolve relative to data/processed roots
            possible_paths = [
                get_data_path() / key,
                get_processed_path() / key,
                Path(key)
            ]
            file_path = next((p for p in possible_paths if p.exists()), None)
        else:
            file_path = Path(key)

        if file_path and file_path.exists():
            try:
                current_hash = calculate_sha256(file_path)
                results[key] = current_hash == record["hash"]
            except Exception:
                results[key] = False
        else:
            results[key] = False

    return results


def clean_state_file(state_path: Path, files_to_keep: List[str]) -> None:
    """
    Remove checksum entries for files that are no longer in the keep list.

    Args:
        state_path: Path to the state JSON file
        files_to_keep: List of relative/absolute paths to retain
    """
    if not state_path.exists():
        return

    with StateLock(state_path):
        state_data = load_checksums(state_path)
        current_checksums = state_data.get("checksums", {})

        # Normalize keep list to strings
        keep_keys = {str(p) for p in files_to_keep}

        # Filter out entries not in keep list
        filtered_checksums = {
            k: v for k, v in current_checksums.items()
            if k in keep_keys
        }

        state_data["checksums"] = filtered_checksums
        save_checksums(state_path, state_data)


def get_state_summary(state_path: Path) -> Dict[str, Any]:
    """
    Generate a summary of the current state file.

    Args:
        state_path: Path to the state JSON file

    Returns:
        Dictionary containing summary statistics
    """
    if not state_path.exists():
        return {
            "exists": False,
            "file_count": 0,
            "total_size_bytes": 0,
            "last_updated": None
        }

    with StateLock(state_path):
        state_data = load_checksums(state_path)

    checksums = state_data.get("checksums", {})
    total_size = sum(
        record.get("size_bytes", 0)
        for record in checksums.values()
    )

    return {
        "exists": True,
        "file_count": len(checksums),
        "total_size_bytes": total_size,
        "last_updated": state_data.get("updated_at"),
        "version": state_data.get("version")
    }
