"""
Hashing utilities for artifact integrity verification (Constitution Principle V).
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Union

def compute_string_hash(s: str, algorithm: str = 'sha256') -> str:
    """Compute hash of a string."""
    hasher = hashlib.new(algorithm)
    hasher.update(s.encode('utf-8'))
    return hasher.hexdigest()

def compute_bytes_hash(data: bytes, algorithm: str = 'sha256') -> str:
    """Compute hash of bytes."""
    hasher = hashlib.new(algorithm)
    hasher.update(data)
    return hasher.hexdigest()

def compute_file_hash(path: Union[str, Path], algorithm: str = 'sha256', chunk_size: int = 8192) -> str:
    """
    Compute hash of a file by reading in chunks.
    
    Args:
        path: Path to file
        algorithm: Hash algorithm (default: sha256)
        chunk_size: Size of chunks to read
    
    Returns:
        Hex digest of the file hash.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    hasher = hashlib.new(algorithm)
    with open(path, 'rb') as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()

def compute_dict_hash(data: Dict[str, Any], algorithm: str = 'sha256') -> str:
    """
    Compute hash of a dictionary by serializing with sorted keys.
    
    Args:
        data: Dictionary to hash
        algorithm: Hash algorithm
    
    Returns:
        Hex digest of the dictionary hash.
    """
    # Sort keys to ensure deterministic serialization
    serialized = json.dumps(data, sort_keys=True, ensure_ascii=True).encode('utf-8')
    return compute_bytes_hash(serialized, algorithm)

def hash_artifact(artifact: Dict[str, Any], include_metadata: bool = True) -> str:
    """
    Generate a content hash for an artifact dictionary.
    
    Args:
        artifact: Artifact dictionary
        include_metadata: Whether to include metadata fields in hash
    
    Returns:
        Hash string.
    """
    if include_metadata:
        return compute_dict_hash(artifact)
    else:
        # Exclude common metadata fields
        filtered = {k: v for k, v in artifact.items() if k not in ['timestamp', 'version', 'metadata']}
        return compute_dict_hash(filtered)

def verify_file_hash(path: Union[str, Path], expected_hash: str, algorithm: str = 'sha256') -> bool:
    """
    Verify a file's hash against an expected value.
    
    Args:
        path: Path to file
        expected_hash: Expected hash string
        algorithm: Hash algorithm
    
    Returns:
        True if hash matches, False otherwise.
    """
    actual_hash = compute_file_hash(path, algorithm)
    return actual_hash == expected_hash
