"""
Configuration utilities for the project.
Provides checksum computation, directory management, and configuration loading.
"""
import os
from pathlib import Path
import hashlib
import json
from typing import List, Tuple, Dict, Any
import random

def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to checksum
        algorithm: Hash algorithm to use (default: sha256)
    
    Returns:
        Hexadecimal string of the checksum
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hasher = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    return hasher.hexdigest()

def compute_directory_checksum(directory_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute a combined checksum for all files in a directory.
    
    Args:
        directory_path: Path to the directory
        algorithm: Hash algorithm to use
    
    Returns:
        Hexadecimal string of the combined checksum
    """
    if not directory_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    
    hasher = hashlib.new(algorithm)
    
    # Sort files for consistent ordering
    files = sorted([f for f in directory_path.rglob('*') if f.is_file() and f.name != ".gitkeep"])
    
    for file_path in files:
        rel_path = file_path.relative_to(directory_path)
        hasher.update(str(rel_path).encode())
        file_hash = compute_file_checksum(file_path, algorithm)
        hasher.update(file_hash.encode())
    
    return hasher.hexdigest()

def save_checksums(checksums: Dict[str, str], output_path: Path) -> None:
    """
    Save checksums to a JSON file.
    
    Args:
        checksums: Dictionary mapping file paths to checksums
        output_path: Path to save the checksums file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(checksums, f, indent=2)

def load_checksums(input_path: Path) -> Dict[str, str]:
    """
    Load checksums from a JSON file.
    
    Args:
        input_path: Path to the checksums file
    
    Returns:
        Dictionary mapping file paths to checksums
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Checksums file not found: {input_path}")
    
    with open(input_path, 'r') as f:
        return json.load(f)

def verify_checksums(checksums_file: Path, base_path: Path) -> bool:
    """
    Verify files against stored checksums.
    
    Args:
        checksums_file: Path to the checksums file
        base_path: Base path for relative file paths
    
    Returns:
        True if all checksums verify, False otherwise
    """
    checksums = load_checksums(checksums_file)
    all_valid = True
    
    for rel_path, expected_checksum in checksums.items():
        file_path = base_path / rel_path
        if not file_path.exists():
            print(f"MISSING: {rel_path}")
            all_valid = False
            continue
        
        actual_checksum = compute_file_checksum(file_path)
        if actual_checksum != expected_checksum:
            print(f"INVALID: {rel_path}")
            print(f"  Expected: {expected_checksum}")
            print(f"  Actual:   {actual_checksum}")
            all_valid = False
        else:
            print(f"OK: {rel_path}")
    
    return all_valid

def ensure_dirs(*paths: Path) -> None:
    """
    Ensure directories exist, creating them if necessary.
    
    Args:
        *paths: Variable number of path objects to ensure
    """
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)
