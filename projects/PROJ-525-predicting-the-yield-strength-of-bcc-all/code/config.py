"""
Configuration module for the BCC Yield Strength prediction pipeline.

This module re-exports key functions from env_config and adds
checksum utilities.
"""
import os
from pathlib import Path
import hashlib
import json
from typing import List, Tuple, Dict, Any
import random

# Import environment configuration functions
from env_config import (
    is_ci_environment,
    set_base_path,
    get_base_path,
    get_data_path,
    get_raw_data_path,
    get_processed_data_path,
    get_logs_path,
    get_reports_path,
    get_state_path,
    get_specs_path,
    get_resource_limits,
    set_global_seed,
    ensure_dirs,
    setup_logger
)

# --- Checksum Utilities ---

def compute_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Compute the checksum of a single file.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        str: Hexadecimal checksum string.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    hash_func = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def compute_directory_checksum(dir_path: Path, algorithm: str = 'sha256') -> str:
    """
    Compute a combined checksum for all files in a directory.
    
    Args:
        dir_path: Path to the directory.
        algorithm: Hash algorithm to use.
        
    Returns:
        str: Hexadecimal checksum string.
    """
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {dir_path}")
        
    hash_func = hashlib.new(algorithm)
    # Sort files to ensure deterministic order
    files = sorted(dir_path.rglob('*'))
    
    for file_path in files:
        if file_path.is_file():
            # Include relative path in hash
            rel_path = str(file_path.relative_to(dir_path))
            hash_func.update(rel_path.encode('utf-8'))
            hash_func.update(compute_file_checksum(file_path, algorithm).encode('utf-8'))
            
    return hash_func.hexdigest()

def save_checksums(checksums: Dict[str, str], output_path: Path) -> None:
    """
    Save checksums to a JSON file.
    
    Args:
        checksums: Dictionary of file paths to checksums.
        output_path: Path to save the JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(checksums, f, indent=2)

def load_checksums(input_path: Path) -> Dict[str, str]:
    """
    Load checksums from a JSON file.
    
    Args:
        input_path: Path to the JSON file.
        
    Returns:
        Dict[str, str]: Dictionary of file paths to checksums.
    """
    if not input_path.exists():
        return {}
    with open(input_path, 'r') as f:
        return json.load(f)

def verify_checksums(checksums: Dict[str, str], base_path: Path = None) -> List[Tuple[str, bool]]:
    """
    Verify files against a dictionary of checksums.
    
    Args:
        checksums: Dictionary of file paths to expected checksums.
        base_path: Base path to resolve relative file paths.
        
    Returns:
        List[Tuple[str, bool]]: List of (file_path, is_valid) tuples.
    """
    if base_path is None:
        base_path = Path.cwd()
        
    results = []
    for rel_path, expected_checksum in checksums.items():
        file_path = base_path / rel_path
        if not file_path.exists():
            results.append((rel_path, False))
            continue
            
        try:
            actual_checksum = compute_file_checksum(file_path)
            is_valid = (actual_checksum == expected_checksum)
            results.append((rel_path, is_valid))
        except Exception:
            results.append((rel_path, False))
            
    return results

# Initialize base path on module load if not already set
if 'get_base_path' not in dir() or get_base_path() is None:
    set_base_path()

# Ensure standard directories exist
try:
    ensure_dirs()
except Exception:
    # Fail gracefully if directory creation fails (e.g., permissions)
    pass