"""
I/O utilities for file operations, checksum generation, and data persistence.
Implements Principle III: Reproducibility (checksums, deterministic I/O).
"""
import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Union, Dict, Any, Optional, List

from .logging import log_info, log_error, log_warning


def calculate_file_checksum(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
    """
    Calculate the checksum of a file using the specified hashing algorithm.
    
    Args:
        file_path: Path to the file to hash.
        algorithm: Hash algorithm to use (default: 'sha256').
    
    Returns:
        Hexadecimal digest string of the file checksum.
    
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        log_error(f"File not found for checksum: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        hasher = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except ValueError as e:
        log_error(f"Unsupported hash algorithm '{algorithm}': {e}")
        raise
    except Exception as e:
        log_error(f"Error calculating checksum for {file_path}: {e}")
        raise


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
        raise NotADirectoryError(f"Path exists but is not a directory: {dir_path}")
    return dir_path


def write_json_file(file_path: Union[str, Path], data: Dict[str, Any], indent: int = 2) -> None:
    """
    Write a dictionary to a JSON file.
    
    Args:
        file_path: Path to the output file.
        data: Dictionary to serialize to JSON.
        indent: Indentation level for pretty-printing.
    """
    file_path = Path(file_path)
    ensure_directory_exists(file_path.parent)
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, sort_keys=True)
        log_info(f"Successfully wrote JSON file: {file_path}")
    except Exception as e:
        log_error(f"Failed to write JSON file {file_path}: {e}")
        raise


def read_json_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Read a JSON file and return the parsed dictionary.
    
    Args:
        file_path: Path to the input file.
    
    Returns:
        Parsed dictionary from the JSON file.
    
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        log_error(f"JSON file not found: {file_path}")
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        log_error(f"Invalid JSON in file {file_path}: {e}")
        raise
    except Exception as e:
        log_error(f"Failed to read JSON file {file_path}: {e}")
        raise


def write_text_file(file_path: Union[str, Path], content: str, encoding: str = 'utf-8') -> None:
    """
    Write a string to a text file.
    
    Args:
        file_path: Path to the output file.
        content: String content to write.
        encoding: Character encoding to use.
    """
    file_path = Path(file_path)
    ensure_directory_exists(file_path.parent)
    try:
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        log_info(f"Successfully wrote text file: {file_path}")
    except Exception as e:
        log_error(f"Failed to write text file {file_path}: {e}")
        raise


def read_text_file(file_path: Union[str, Path], encoding: str = 'utf-8') -> str:
    """
    Read the full content of a text file.
    
    Args:
        file_path: Path to the input file.
        encoding: Character encoding to use.
    
    Returns:
        String content of the file.
    
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        log_error(f"Text file not found: {file_path}")
        raise FileNotFoundError(f"Text file not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
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


def copy_file(src: Union[str, Path], dst: Union[str, Path]) -> Path:
    """
    Copy a file from source to destination.
    
    Args:
        src: Source file path.
        dst: Destination file path.
    
    Returns:
        Path to the destination file.
    """
    src = Path(src)
    dst = Path(dst)
    if not src.exists():
        log_error(f"Source file not found for copy: {src}")
        raise FileNotFoundError(f"Source file not found: {src}")
    
    ensure_directory_exists(dst.parent)
    try:
        shutil.copy2(src, dst)
        log_info(f"Copied {src} to {dst}")
        return dst
    except Exception as e:
        log_error(f"Failed to copy {src} to {dst}: {e}")
        raise


def delete_file(file_path: Union[str, Path]) -> None:
    """
    Delete a file.
    
    Args:
        file_path: Path to the file to delete.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        log_warning(f"File does not exist, cannot delete: {file_path}")
        return
    
    try:
        file_path.unlink()
        log_info(f"Deleted file: {file_path}")
    except Exception as e:
        log_error(f"Failed to delete file {file_path}: {e}")
        raise


def list_files(dir_path: Union[str, Path], extension: Optional[str] = None) -> List[Path]:
    """
    List all files in a directory, optionally filtered by extension.
    
    Args:
        dir_path: Directory path to scan.
        extension: Optional file extension filter (e.g., '.json').
    
    Returns:
        List of Path objects for matching files.
    """
    dir_path = Path(dir_path)
    if not dir_path.exists() or not dir_path.is_dir():
        log_error(f"Directory does not exist or is not a directory: {dir_path}")
        raise NotADirectoryError(f"Directory does not exist: {dir_path}")
    
    files = []
    for item in dir_path.iterdir():
        if item.is_file():
            if extension is None or item.suffix == extension:
                files.append(item)
    
    log_info(f"Found {len(files)} files in {dir_path}")
    return sorted(files)