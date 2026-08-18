"""
I/O utilities for the llmXive pipeline.
Implements checksum generation and file I/O helpers (Principle III).
"""
import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Union, Dict, Any, Optional, List

from .logging import log_error, log_critical, log_info


def calculate_file_checksum(
    file_path: Union[str, Path],
    algorithm: str = "sha256"
) -> str:
    """
    Calculate the cryptographic checksum of a file.

    Args:
        file_path: Path to the file to hash.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal string of the file checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
        RuntimeError: If an error occurs during hashing.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        log_error(f"File not found for checksum calculation: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        hasher = hashlib.new(algorithm)
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except ValueError as e:
        log_error(f"Unsupported hash algorithm '{algorithm}': {e}")
        raise
    except Exception as e:
        log_critical(f"Failed to calculate checksum for {file_path}: {e}")
        raise RuntimeError(f"Checksum calculation failed: {e}") from e


def ensure_directory_exists(dir_path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        dir_path: Path to the directory.

    Returns:
        The Path object of the directory.
    """
    dir_path = Path(dir_path)
    if not dir_path.exists():
        log_info(f"Creating directory: {dir_path}")
        dir_path.mkdir(parents=True, exist_ok=True)
    elif not dir_path.is_dir():
        log_error(f"Path exists but is not a directory: {dir_path}")
        raise NotADirectoryError(f"Path is not a directory: {dir_path}")
    return dir_path


def write_json_file(
    data: Dict[str, Any],
    file_path: Union[str, Path],
    ensure_dir: bool = True,
    indent: int = 2
) -> Path:
    """
    Write a dictionary to a JSON file.

    Args:
        data: Dictionary to serialize.
        file_path: Target file path.
        ensure_dir: If True, create parent directories if they don't exist.
        indent: Indentation level for pretty-printing.

    Returns:
        The Path object of the written file.
    """
    file_path = Path(file_path)
    if ensure_dir:
        ensure_directory_exists(file_path.parent)

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, sort_keys=True)
        log_info(f"Successfully wrote JSON file: {file_path}")
        return file_path
    except Exception as e:
        log_error(f"Failed to write JSON file {file_path}: {e}")
        raise


def read_json_file(
    file_path: Union[str, Path]
) -> Dict[str, Any]:
    """
    Read a JSON file and return the parsed dictionary.

    Args:
        file_path: Path to the JSON file.

    Returns:
        Parsed dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        log_error(f"JSON file not found: {file_path}")
        raise FileNotFoundError(f"JSON file not found: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        log_info(f"Successfully read JSON file: {file_path}")
        return data
    except json.JSONDecodeError as e:
        log_error(f"Invalid JSON in {file_path}: {e}")
        raise
    except Exception as e:
        log_error(f"Failed to read JSON file {file_path}: {e}")
        raise


def write_text_file(
    content: str,
    file_path: Union[str, Path],
    ensure_dir: bool = True,
    encoding: str = "utf-8"
) -> Path:
    """
    Write a string to a text file.

    Args:
        content: String content to write.
        file_path: Target file path.
        ensure_dir: If True, create parent directories if they don't exist.
        encoding: File encoding.

    Returns:
        The Path object of the written file.
    """
    file_path = Path(file_path)
    if ensure_dir:
        ensure_directory_exists(file_path.parent)

    try:
        with open(file_path, "w", encoding=encoding) as f:
            f.write(content)
        log_info(f"Successfully wrote text file: {file_path}")
        return file_path
    except Exception as e:
        log_error(f"Failed to write text file {file_path}: {e}")
        raise


def read_text_file(
    file_path: Union[str, Path],
    encoding: str = "utf-8"
) -> str:
    """
    Read a text file and return its content as a string.

    Args:
        file_path: Path to the text file.
        encoding: File encoding.

    Returns:
        File content as a string.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        log_error(f"Text file not found: {file_path}")
        raise FileNotFoundError(f"Text file not found: {file_path}")

    try:
        with open(file_path, "r", encoding=encoding) as f:
            content = f.read()
        log_info(f"Successfully read text file: {file_path}")
        return content
    except Exception as e:
        log_error(f"Failed to read text file {file_path}: {e}")
        raise


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
        log_error(f"File not found for size check: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    return file_path.stat().st_size
