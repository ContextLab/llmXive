"""
Data I/O utilities for the llmXive pipeline.

This module provides robust utilities for:
- Checksumming files (SHA-256)
- Safe path handling (validation, normalization)
- JSON and CSV serialization/deserialization
- Directory management

All operations follow the "FAIL LOUDLY" policy:
- Missing files raise FileNotFoundError
- Invalid data raises ValueError or specific parsing errors
- No silent fallbacks or synthetic data generation
"""
import hashlib
import json
import os
import csv
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

# Constants
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
CHECKSUM_ALGORITHM = "sha256"
DEFAULT_ENCODING = "utf-8"


def validate_project_path(path: Union[str, Path], must_exist: bool = True) -> Path:
    """
    Validate and normalize a project path.

    Args:
        path: The path to validate (string or Path object)
        must_exist: If True, raise FileNotFoundError if path doesn't exist

    Returns:
        Normalized Path object relative to project root

    Raises:
        ValueError: If path is outside project root or invalid
        FileNotFoundError: If must_exist=True and path doesn't exist
    """
    path_obj = Path(path)

    # Resolve to absolute path
    if path_obj.is_absolute():
        normalized = path_obj.resolve()
    else:
        normalized = (PROJECT_ROOT / path_obj).resolve()

    # Ensure path is within project root
    try:
        normalized.relative_to(PROJECT_ROOT)
    except ValueError:
        raise ValueError(f"Path {path} is outside project root {PROJECT_ROOT}")

    # Check existence if required
    if must_exist and not normalized.exists():
        raise FileNotFoundError(f"Required path does not exist: {normalized}")

    return normalized


def compute_file_checksum(
    file_path: Union[str, Path],
    algorithm: str = CHECKSUM_ALGORITHM,
    chunk_size: int = 8192
) -> str:
    """
    Compute SHA-256 checksum of a file.

    Args:
        file_path: Path to the file
        algorithm: Hash algorithm (default: sha256)
        chunk_size: Size of chunks to read (default: 8KB)

    Returns:
        Hexadecimal checksum string

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If unsupported algorithm specified
    """
    path_obj = validate_project_path(file_path, must_exist=True)

    if algorithm.lower() not in hashlib.algorithms_available:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")

    hasher = hashlib.new(algorithm)

    with open(path_obj, 'rb') as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)

    return hasher.hexdigest()


def verify_checksum(
    file_path: Union[str, Path],
    expected_checksum: str,
    algorithm: str = CHECKSUM_ALGORITHM
) -> bool:
    """
    Verify a file's checksum against an expected value.

    Args:
        file_path: Path to the file
        expected_checksum: Expected checksum string
        algorithm: Hash algorithm to use

    Returns:
        True if checksum matches

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If checksums don't match
    """
    actual_checksum = compute_file_checksum(file_path, algorithm)

    if actual_checksum.lower() != expected_checksum.lower():
        raise ValueError(
            f"Checksum mismatch for {file_path}\n"
            f"Expected: {expected_checksum}\n"
            f"Actual:   {actual_checksum}"
        )

    return True


def save_json(
    data: Any,
    file_path: Union[str, Path],
    indent: int = 2,
    ensure_ascii: bool = False,
    create_dirs: bool = True
) -> Path:
    """
    Save data to a JSON file.

    Args:
        data: Data to serialize (must be JSON-serializable)
        file_path: Output file path
        indent: JSON indentation level
        ensure_ascii: If True, escape non-ASCII characters
        create_dirs: If True, create parent directories

    Returns:
        Path to the created file

    Raises:
        TypeError: If data is not JSON-serializable
        OSError: If file cannot be written
    """
    path_obj = Path(file_path)

    if create_dirs:
        path_obj.parent.mkdir(parents=True, exist_ok=True)

    # Validate path is within project
    validate_project_path(path_obj, must_exist=False)

    with open(path_obj, 'w', encoding=DEFAULT_ENCODING) as f:
        json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)

    return path_obj


def load_json(
    file_path: Union[str, Path],
    required: bool = True
) -> Any:
    """
    Load data from a JSON file.

    Args:
        file_path: Input file path
        required: If False, return None if file doesn't exist

    Returns:
        Deserialized data

    Raises:
        FileNotFoundError: If file doesn't exist and required=True
        json.JSONDecodeError: If file contains invalid JSON
    """
    path_obj = validate_project_path(file_path, must_exist=required)

    if not required and not path_obj.exists():
        return None

    with open(path_obj, 'r', encoding=DEFAULT_ENCODING) as f:
        return json.load(f)


def save_csv(
    data: List[Dict[str, Any]],
    file_path: Union[str, Path],
    fieldnames: Optional[List[str]] = None,
    create_dirs: bool = True
) -> Path:
    """
    Save a list of dictionaries to a CSV file.

    Args:
        data: List of dictionaries to save
        file_path: Output file path
        fieldnames: Column names (auto-detected if None)
        create_dirs: If True, create parent directories

    Returns:
        Path to the created file

    Raises:
        ValueError: If data is empty or inconsistent
        OSError: If file cannot be written
    """
    if not data:
        raise ValueError("Cannot save empty CSV data")

    # Determine fieldnames
    if fieldnames is None:
        fieldnames = list(data[0].keys())
        # Verify all rows have consistent keys
        for i, row in enumerate(data):
            if set(row.keys()) != set(fieldnames):
                raise ValueError(
                    f"Row {i} has inconsistent keys: {set(row.keys())} vs {set(fieldnames)}"
                )

    path_obj = Path(file_path)

    if create_dirs:
        path_obj.parent.mkdir(parents=True, exist_ok=True)

    validate_project_path(path_obj, must_exist=False)

    with open(path_obj, 'w', newline='', encoding=DEFAULT_ENCODING) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    return path_obj


def load_csv(
    file_path: Union[str, Path],
    required: bool = True,
    convert_types: bool = True
) -> List[Dict[str, Any]]:
    """
    Load data from a CSV file.

    Args:
        file_path: Input file path
        required: If False, return empty list if file doesn't exist
        convert_types: If True, attempt to convert numeric values

    Returns:
        List of dictionaries

    Raises:
        FileNotFoundError: If file doesn't exist and required=True
        csv.Error: If CSV is malformed
    """
    path_obj = validate_project_path(file_path, must_exist=required)

    if not required and not path_obj.exists():
        return []

    data = []

    def convert_value(value: str) -> Any:
        """Attempt to convert string to appropriate type."""
        if value == '' or value is None:
            return None
        # Try integer
        try:
            return int(value)
        except ValueError:
            pass
        # Try float
        try:
            return float(value)
        except ValueError:
            pass
        # Return as string
        return value

    with open(path_obj, 'r', encoding=DEFAULT_ENCODING) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if convert_types:
                row = {k: convert_value(v) for k, v in row.items()}
            data.append(row)

    return data


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path

    Returns:
        Path to the directory

    Raises:
        OSError: If directory cannot be created
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    validate_project_path(path_obj, must_exist=True)
    return path_obj


def get_file_size(path: Union[str, Path]) -> int:
    """
    Get file size in bytes.

    Args:
        path: File path

    Returns:
        File size in bytes

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    path_obj = validate_project_path(path, must_exist=True)
    return path_obj.stat().st_size


def list_files(
    directory: Union[str, Path],
    pattern: Optional[str] = None,
    recursive: bool = False
) -> List[Path]:
    """
    List files in a directory.

    Args:
        directory: Directory path
        pattern: Glob pattern to filter files (e.g., '*.csv')
        recursive: If True, search subdirectories

    Returns:
        List of matching file paths

    Raises:
        NotADirectoryError: If path is not a directory
    """
    dir_obj = validate_project_path(directory, must_exist=True)

    if not dir_obj.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {dir_obj}")

    if pattern:
        if recursive:
            return list(dir_obj.rglob(pattern))
        else:
            return list(dir_obj.glob(pattern))
    else:
        if recursive:
            return [p for p in dir_obj.rglob('*') if p.is_file()]
        else:
            return [p for p in dir_obj.iterdir() if p.is_file()]


def atomic_write(
    content: Union[str, bytes],
    file_path: Union[str, Path],
    mode: str = 'w',
    encoding: Optional[str] = DEFAULT_ENCODING
) -> Path:
    """
    Write content to a file atomically (write to temp, then rename).

    Args:
        content: Content to write (string or bytes)
        file_path: Output file path
        mode: Write mode ('w' or 'wb')
        encoding: Encoding for text mode

    Returns:
        Path to the created file

    Raises:
        OSError: If write fails
    """
    path_obj = Path(file_path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    validate_project_path(path_obj, must_exist=False)

    # Create temp file in same directory for atomic rename
    temp_path = path_obj.with_suffix(path_obj.suffix + '.tmp')

    try:
        if 'b' in mode:
            if isinstance(content, str):
                content = content.encode(encoding or DEFAULT_ENCODING)
            with open(temp_path, 'wb') as f:
                f.write(content)
        else:
            with open(temp_path, 'w', encoding=encoding) as f:
                f.write(content)

        # Atomic rename
        temp_path.replace(path_obj)

    except Exception as e:
        # Clean up temp file on failure
        if temp_path.exists():
            temp_path.unlink()
        raise OSError(f"Failed to write {file_path}: {e}")

    return path_obj


def get_relative_path(path: Union[str, Path]) -> Path:
    """
    Get path relative to project root.

    Args:
        path: Absolute or relative path

    Returns:
        Path relative to project root

    Raises:
        ValueError: If path is outside project root
    """
    path_obj = Path(path)
    if path_obj.is_absolute():
        path_obj = path_obj.resolve()
        return path_obj.relative_to(PROJECT_ROOT)
    else:
        return path_obj


def save_metadata(
    metadata: Dict[str, Any],
    file_path: Union[str, Path],
    include_timestamp: bool = True
) -> Path:
    """
    Save metadata with optional timestamp.

    Args:
        metadata: Metadata dictionary
        file_path: Output file path
        include_timestamp: If True, add 'created_at' field

    Returns:
        Path to the created file
    """
    if include_timestamp:
        metadata['created_at'] = datetime.utcnow().isoformat()

    return save_json(metadata, file_path)


def load_metadata(file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """
    Load metadata file.

    Args:
        file_path: Input file path

    Returns:
        Metadata dictionary or None if file doesn't exist
    """
    return load_json(file_path, required=False)
