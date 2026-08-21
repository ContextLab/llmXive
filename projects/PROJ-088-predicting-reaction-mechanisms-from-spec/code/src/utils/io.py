"""
I/O utilities for the llmXive science pipeline.

Implements checksum generation and file I/O helpers adhering to
Principle III (Data Integrity and Reproducibility).
"""
import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Union, Dict, Any, Optional, List


def calculate_file_checksum(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
    """
    Calculate the cryptographic checksum of a file.
    
    Args:
        file_path: Path to the file to hash.
        algorithm: Hash algorithm to use (default: 'sha256').
        
    Returns:
        Hexadecimal string of the file checksum.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    hash_obj = hashlib.new(algorithm)
    
    try:
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(8192), b''):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file {file_path} for checksum: {e}")


def ensure_directory_exists(dir_path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        dir_path: Path to the directory.
        
    Returns:
        The Path object of the ensured directory.
    """
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json_file(file_path: Union[str, Path], data: Dict[str, Any], indent: int = 2) -> Path:
    """
    Write a dictionary to a JSON file.
    
    Args:
        file_path: Path to the output file.
        data: Dictionary to serialize.
        indent: Indentation level for pretty printing.
        
    Returns:
        The Path object of the written file.
    """
    path = Path(file_path)
    ensure_directory_exists(path.parent)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, sort_keys=True)
        
    return path


def read_json_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Read a JSON file and return its contents as a dictionary.
    
    Args:
        file_path: Path to the input file.
        
    Returns:
        Dictionary containing the JSON data.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")
        
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_text_file(file_path: Union[str, Path], content: str) -> Path:
    """
    Write a string to a text file.
    
    Args:
        file_path: Path to the output file.
        content: String content to write.
        
    Returns:
        The Path object of the written file.
    """
    path = Path(file_path)
    ensure_directory_exists(path.parent)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    return path


def read_text_file(file_path: Union[str, Path]) -> str:
    """
    Read a text file and return its contents as a string.
    
    Args:
        file_path: Path to the input file.
        
    Returns:
        String content of the file.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Text file not found: {file_path}")
        
    with open(path, 'r', encoding='utf-8') as f:
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
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    return path.stat().st_size
