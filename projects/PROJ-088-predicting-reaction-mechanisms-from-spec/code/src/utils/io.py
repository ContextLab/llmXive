"""
I/O utilities for file operations and checksum generation.
Implements Principle III: Data Integrity and Reproducibility.
"""
import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Union, Dict, Any, Optional, List

# Constants
DEFAULT_CHECKSUM_ALGORITHM = 'sha256'
CHUNK_SIZE = 8192  # 8KB chunks for reading large files


def calculate_file_checksum(file_path: Union[str, Path], algorithm: str = DEFAULT_CHECKSUM_ALGORITHM) -> str:
    """
    Calculate the checksum of a file using the specified algorithm.

    Args:
        file_path: Path to the file to calculate checksum for.
        algorithm: Hash algorithm to use (default: 'sha256').

    Returns:
        Hexadecimal digest string of the file's checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        hasher = hashlib.new(algorithm)
    except ValueError:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")

    with open(file_path, 'rb') as f:
        while chunk := f.read(CHUNK_SIZE):
            hasher.update(chunk)

    return hasher.hexdigest()


def ensure_directory_exists(dir_path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        dir_path: Path to the directory to ensure exists.

    Returns:
        The Path object for the directory.
    """
    dir_path = Path(dir_path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def write_json_file(data: Dict[str, Any], file_path: Union[str, Path], ensure_dir: bool = True) -> Path:
    """
    Write a dictionary to a JSON file.

    Args:
        data: Dictionary to write to the file.
        file_path: Path to the output JSON file.
        ensure_dir: If True, create parent directories if they don't exist.

    Returns:
        The Path object for the written file.

    Raises:
        TypeError: If the data is not JSON serializable.
    """
    file_path = Path(file_path)
    if ensure_dir:
        ensure_directory_exists(file_path.parent)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, sort_keys=True)

    return file_path


def read_json_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Read a JSON file and return its contents as a dictionary.

    Args:
        file_path: Path to the JSON file to read.

    Returns:
        Dictionary containing the JSON data.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_text_file(content: str, file_path: Union[str, Path], ensure_dir: bool = True) -> Path:
    """
    Write a string to a text file.

    Args:
        content: String content to write.
        file_path: Path to the output text file.
        ensure_dir: If True, create parent directories if they don't exist.

    Returns:
        The Path object for the written file.
    """
    file_path = Path(file_path)
    if ensure_dir:
        ensure_directory_exists(file_path.parent)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return file_path


def read_text_file(file_path: Union[str, Path]) -> str:
    """
    Read a text file and return its contents as a string.

    Args:
        file_path: Path to the text file to read.

    Returns:
        String content of the file.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Text file not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def get_file_size(file_path: Union[str, Path]) -> int:
    """
    Get the size of a file in bytes.

    Args:
        file_path: Path to the file.

    Returns:
        File size in bytes.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    return file_path.stat().st_size


def copy_file(src: Union[str, Path], dst: Union[str, Path], ensure_dir: bool = True) -> Path:
    """
    Copy a file from source to destination.

    Args:
        src: Source file path.
        dst: Destination file path.
        ensure_dir: If True, create parent directories for destination if they don't exist.

    Returns:
        The Path object for the destination file.

    Raises:
        FileNotFoundError: If the source file does not exist.
    """
    src = Path(src)
    dst = Path(dst)

    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {src}")

    if ensure_dir:
        ensure_directory_exists(dst.parent)

    shutil.copy2(src, dst)
    return dst


def delete_file(file_path: Union[str, Path]) -> bool:
    """
    Delete a file.

    Args:
        file_path: Path to the file to delete.

    Returns:
        True if the file was deleted, False if it didn't exist.

    Raises:
        PermissionError: If the file cannot be deleted due to permissions.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return False

    file_path.unlink()
    return True


def list_files(directory: Union[str, Path], extension: Optional[str] = None) -> List[Path]:
    """
    List all files in a directory, optionally filtered by extension.

    Args:
        directory: Path to the directory to list files from.
        extension: Optional file extension to filter by (e.g., '.json').

    Returns:
        List of Path objects for matching files.

    Raises:
        NotADirectoryError: If the path is not a directory.
    """
    directory = Path(directory)
    if not directory.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {directory}")

    if extension:
        if not extension.startswith('.'):
            extension = f'.{extension}'
        return list(directory.glob(f'*{extension}'))

    return [f for f in directory.iterdir() if f.is_file()]