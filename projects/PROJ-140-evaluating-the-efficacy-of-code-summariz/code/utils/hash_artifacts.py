"""
Artifact hashing utilities for versioning and reproducibility.

Provides functions to compute SHA-256 hashes of files and directories
to ensure data integrity and reproducibility.
"""
import hashlib
import os
from pathlib import Path
from typing import Optional, Dict, List
import json

def hash_file(file_path: str, algorithm: str = 'sha256') -> str:
    """
    Compute SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm (default: sha256)
    
    Returns:
        Hexadecimal hash string
    
    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_obj = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b''):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()

def hash_directory(dir_path: str, algorithm: str = 'sha256', 
                   exclude_patterns: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Compute SHA-256 hashes for all files in a directory.
    
    Args:
        dir_path: Path to the directory
        algorithm: Hash algorithm (default: sha256)
        exclude_patterns: List of patterns to exclude (e.g., ['*.pyc', '__pycache__'])
    
    Returns:
        Dictionary mapping relative file paths to their hashes
    
    Raises:
        NotADirectoryError: If path is not a directory
    """
    dir_path = Path(dir_path)
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {dir_path}")
    
    if exclude_patterns is None:
        exclude_patterns = ['*.pyc', '__pycache__', '.git', '.env']
    
    hashes = {}
    
    for file_path in dir_path.rglob('*'):
        if file_path.is_file():
            # Check if file should be excluded
            relative_path = str(file_path.relative_to(dir_path))
            should_exclude = False
            
            for pattern in exclude_patterns:
                if pattern.startswith('.'):
                    # Handle hidden files/directories
                    if relative_path.startswith(pattern) or f'/{pattern}' in relative_path:
                        should_exclude = True
                        break
                else:
                    # Handle file extensions
                    if file_path.suffix == pattern or file_path.name == pattern:
                        should_exclude = True
                        break
            
            if not should_exclude:
                try:
                    hashes[relative_path] = hash_file(file_path, algorithm)
                except (FileNotFoundError, IOError) as e:
                    # Skip files that can't be read
                    print(f"Warning: Could not hash {file_path}: {e}")
    
    return hashes

def verify_file_hash(file_path: str, expected_hash: str, 
                     algorithm: str = 'sha256') -> bool:
    """
    Verify that a file's hash matches the expected value.
    
    Args:
        file_path: Path to the file
        expected_hash: Expected hash value
        algorithm: Hash algorithm (default: sha256)
    
    Returns:
        True if hash matches, False otherwise
    """
    try:
        actual_hash = hash_file(file_path, algorithm)
        return actual_hash.lower() == expected_hash.lower()
    except (FileNotFoundError, IOError):
        return False

def save_hashes(hashes: Dict[str, str], output_path: str) -> None:
    """
    Save hash dictionary to a JSON file.
    
    Args:
        hashes: Dictionary of file paths to hashes
        output_path: Path to output JSON file
    """
    with open(output_path, 'w') as f:
        json.dump(hashes, f, indent=2)

def load_hashes(input_path: str) -> Dict[str, str]:
    """
    Load hash dictionary from a JSON file.
    
    Args:
        input_path: Path to input JSON file
    
    Returns:
        Dictionary of file paths to hashes
    """
    with open(input_path, 'r') as f:
        return json.load(f)

def generate_manifest(dir_path: str, output_path: str, 
                     exclude_patterns: Optional[List[str]] = None) -> str:
    """
    Generate a manifest file with hashes for all files in a directory.
    
    Args:
        dir_path: Path to the directory
        output_path: Path to save manifest file
        exclude_patterns: List of patterns to exclude
    
    Returns:
        Path to the generated manifest file
    """
    hashes = hash_directory(dir_path, exclude_patterns=exclude_patterns)
    save_hashes(hashes, output_path)
    return output_path