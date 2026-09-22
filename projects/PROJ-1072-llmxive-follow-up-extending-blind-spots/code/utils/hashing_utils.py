import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Union

def compute_string_hash(s: str, algorithm: str = "sha256") -> str:
    """
    Compute the hash of a string.
    
    Args:
        s: Input string.
        algorithm: Hash algorithm to use.
        
    Returns:
        Hexadecimal hash string.
    """
    hasher = hashlib.new(algorithm)
    hasher.update(s.encode('utf-8'))
    return hasher.hexdigest()

def compute_bytes_hash(data: bytes, algorithm: str = "sha256") -> str:
    """
    Compute the hash of bytes.
    
    Args:
        data: Input bytes.
        algorithm: Hash algorithm.
        
    Returns:
        Hexadecimal hash string.
    """
    hasher = hashlib.new(algorithm)
    hasher.update(data)
    return hasher.hexdigest()

def compute_file_hash(file_path: Union[str, Path], algorithm: str = "sha256", chunk_size: int = 8192) -> str:
    """
    Compute the hash of a file.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm.
        chunk_size: Size of chunks to read.
        
    Returns:
        Hexadecimal hash string.
    """
    hasher = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            hasher.update(chunk)
    return hasher.hexdigest()

def compute_dict_hash(d: Dict[str, Any], algorithm: str = "sha256") -> str:
    """
    Compute the hash of a dictionary (sorted keys for consistency).
    
    Args:
        d: Input dictionary.
        algorithm: Hash algorithm.
        
    Returns:
        Hexadecimal hash string.
    """
    # Serialize with sorted keys to ensure consistency
    serialized = json.dumps(d, sort_keys=True, ensure_ascii=False)
    return compute_string_hash(serialized, algorithm)

def hash_artifact(artifact: Union[str, bytes, Path, Dict[str, Any]], algorithm: str = "sha256") -> str:
    """
    Compute hash based on artifact type.
    
    Args:
        artifact: String, bytes, file path, or dictionary.
        algorithm: Hash algorithm.
        
    Returns:
        Hexadecimal hash string.
    """
    if isinstance(artifact, str):
        return compute_string_hash(artifact, algorithm)
    elif isinstance(artifact, bytes):
        return compute_bytes_hash(artifact, algorithm)
    elif isinstance(artifact, (Path, str)):
        return compute_file_hash(artifact, algorithm)
    elif isinstance(artifact, dict):
        return compute_dict_hash(artifact, algorithm)
    else:
        raise TypeError(f"Unsupported artifact type: {type(artifact)}")

def verify_file_hash(file_path: Union[str, Path], expected_hash: str, algorithm: str = "sha256") -> bool:
    """
    Verify the hash of a file against an expected value.
    
    Args:
        file_path: Path to the file.
        expected_hash: Expected hash string.
        algorithm: Hash algorithm.
        
    Returns:
        True if hashes match, False otherwise.
    """
    actual_hash = compute_file_hash(file_path, algorithm)
    return actual_hash == expected_hash
