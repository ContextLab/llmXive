"""
I/O utilities for the MD simulation pipeline.

Provides:
- SHA256 checksumming for data integrity (Principle V)
- Safe file I/O operations
- State management for tracking processed files
"""
import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, Optional, Union


def compute_sha256(file_path: Union[str, Path]) -> str:
    """
    Compute the SHA256 checksum of a file.

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
        raise FileNotFoundError(f"File not found: {path}")
    
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Failed to read file for checksum: {path}") from e


def write_json(data: Dict[str, Any], file_path: Union[str, Path], indent: int = 2) -> None:
    """
    Write data to a JSON file atomically.

    Args:
        data: Dictionary to serialize.
        file_path: Destination path.
        indent: JSON indentation level.

    Raises:
        IOError: If the file cannot be written.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    temp_path = path.with_suffix(".tmp")
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, sort_keys=True)
        shutil.move(temp_path, path)
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        raise IOError(f"Failed to write JSON file: {path}") from e


def read_json(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Read data from a JSON file.

    Args:
        file_path: Path to the JSON file.

    Returns:
        Parsed dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_directory(dir_path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        dir_path: Path to the directory.

    Returns:
        The Path object for the directory.
    """
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def update_state(
    state_file: Union[str, Path],
    key: str,
    value: Any,
    checksum_file: Optional[Union[str, Path]] = None
) -> None:
    """
    Update a state tracking file with a new key-value pair.
    Optionally computes and stores a checksum for the value if it is a file path.

    This implements Principle V: Data Integrity via persistent state tracking.

    Args:
        state_file: Path to the JSON state file.
        key: The key to update.
        value: The value to store.
        checksum_file: If provided and `value` is a string path to a file,
                       compute its SHA256 and store it under `{key}_checksum`.
    """
    state_path = Path(state_file)
    state_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing state or initialize empty
    if state_path.exists():
        state = read_json(state_path)
    else:
        state = {}

    # Update the value
    state[key] = value

    # Handle checksum if requested
    if checksum_file:
        checksum_path = Path(checksum_file)
        checksum_key = f"{key}_checksum"
        if isinstance(value, str) and Path(value).exists():
            state[checksum_key] = compute_sha256(value)
        else:
            # If value is not a file or doesn't exist, clear the checksum
            if checksum_key in state:
                del state[checksum_key]

    write_json(state, state_path)


def verify_checksum(file_path: Union[str, Path], expected_checksum: str) -> bool:
    """
    Verify a file's checksum against an expected value.

    Args:
        file_path: Path to the file to verify.
        expected_checksum: The expected SHA256 hex string.

    Returns:
        True if checksums match, False otherwise.
    """
    actual = compute_sha256(file_path)
    return actual == expected_checksum


def safe_copy(source: Union[str, Path], destination: Union[str, Path]) -> Path:
    """
    Safely copy a file, creating parent directories if needed.

    Args:
        source: Source file path.
        destination: Destination file path.

    Returns:
        Path to the destination file.

    Raises:
        FileNotFoundError: If source does not exist.
        IOError: If copy fails.
    """
    src = Path(source)
    dst = Path(destination)
    
    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {src}")
    
    dst.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        shutil.copy2(src, dst)
        return dst
    except Exception as e:
        raise IOError(f"Failed to copy {src} to {dst}") from e
