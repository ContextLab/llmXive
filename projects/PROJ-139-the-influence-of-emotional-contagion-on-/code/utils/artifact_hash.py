import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union
from datetime import datetime

def compute_file_hash(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Computes the hash of a file's contents.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        Hexadecimal digest of the file hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    hasher = hashlib.new(algorithm)
    with open(path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    
    return hasher.hexdigest()

def compute_directory_hash(dir_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Computes a deterministic hash for a directory based on its structure and file contents.
    Files are processed in sorted order to ensure reproducibility.
    
    Args:
        dir_path: Path to the directory.
        algorithm: Hash algorithm to use.
        
    Returns:
        Hexadecimal digest of the directory hash.
        
    Raises:
        NotADirectoryError: If the path is not a directory.
    """
    path = Path(dir_path)
    if not path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {path}")

    hasher = hashlib.new(algorithm)
    
    # Get all files, sorted by relative path for determinism
    files = sorted(path.rglob("*"))
    
    # Hash the file count first
    hasher.update(str(len(files)).encode('utf-8'))

    for file_path in files:
        if file_path.is_file():
            # Include relative path in hash
            rel_path = file_path.relative_to(path)
            hasher.update(str(rel_path).encode('utf-8'))
            
            # Include file content hash
            file_hash = compute_file_hash(file_path, algorithm)
            hasher.update(file_hash.encode('utf-8'))

    return hasher.hexdigest()

def hash_artifact(artifact_path: Union[str, Path]) -> Dict[str, str]:
    """
    Generates a hash manifest for a given artifact (file or directory).
    
    Args:
        artifact_path: Path to the artifact.
        
    Returns:
        Dictionary containing:
            - path: Absolute path string
            - type: 'file' or 'directory'
            - hash: The computed hash
            - timestamp: ISO format timestamp of hashing
    """
    path = Path(artifact_path)
    if not path.exists():
        raise FileNotFoundError(f"Artifact not found: {path}")

    if path.is_file():
        h = compute_file_hash(path)
        artifact_type = "file"
    elif path.is_dir():
        h = compute_directory_hash(path)
        artifact_type = "directory"
    else:
        raise ValueError(f"Unsupported artifact type: {path}")

    return {
        "path": str(path.resolve()),
        "type": artifact_type,
        "hash": h,
        "timestamp": datetime.now().isoformat()
    }

def verify_artifact(artifact_path: Union[str, Path], expected_hash: str) -> bool:
    """
    Verifies the integrity of an artifact by comparing its current hash to an expected hash.
    
    Args:
        artifact_path: Path to the artifact.
        expected_hash: The expected hash value.
        
    Returns:
        True if the hash matches, False otherwise.
        
    Raises:
        FileNotFoundError: If the artifact does not exist.
    """
    path = Path(artifact_path)
    if not path.exists():
        raise FileNotFoundError(f"Artifact not found for verification: {path}")

    if path.is_file():
        current_hash = compute_file_hash(path)
    elif path.is_dir():
        current_hash = compute_directory_hash(path)
    else:
        raise ValueError(f"Unsupported artifact type: {path}")

    return current_hash == expected_hash
