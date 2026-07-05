"""
Data hygiene utilities for checksumming and file validation.

This module provides functions to:
1. Validate the existence of required data files.
2. Compute and verify SHA-256 checksums for data integrity.
3. Generate checksum manifests for derived data.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

# Import global constants from the project's __init__
# Note: Using relative import as per project structure
try:
    from .. import MIN_SAMPLE_SIZE, ALPHA, VIF_THRESHOLD
except (ImportError, ValueError):
    # Fallback for direct execution or if __init__ isn't fully populated yet
    MIN_SAMPLE_SIZE = 30
    ALPHA = 0.05
    VIF_THRESHOLD = 5.0


def compute_sha256(file_path: Union[str, Path], chunk_size: int = 8192) -> str:
    """
    Compute the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file.
        chunk_size: Size of chunks to read at a time.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If the path points to a directory.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if file_path.is_dir():
        raise IsADirectoryError(f"Path is a directory: {file_path}")

    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def validate_file_exists(file_path: Union[str, Path]) -> Tuple[bool, Optional[str]]:
    """
    Check if a specific file exists at the given path.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Tuple of (exists: bool, error_message: Optional[str])
    """
    path = Path(file_path)
    if not path.exists():
        return False, f"File missing: {path.resolve()}"
    if not path.is_file():
        return False, f"Path is not a file: {path.resolve()}"
    return True, None


def validate_files_exist(file_paths: List[Union[str, Path]]) -> Dict[str, bool]:
    """
    Validate a list of file paths.
    
    Args:
        file_paths: List of file paths to check.
        
    Returns:
        Dictionary mapping file path string to boolean existence status.
    """
    results = {}
    for path in file_paths:
        exists, _ = validate_file_exists(path)
        results[str(path)] = exists
    return results


def create_checksum_manifest(
    file_paths: List[Union[str, Path]], 
    output_path: Optional[Union[str, Path]] = None
) -> Dict[str, str]:
    """
    Create a manifest of checksums for a list of files.
    
    Args:
        file_paths: List of files to checksum.
        output_path: Optional path to save the manifest as JSON.
        
    Returns:
        Dictionary mapping file paths to their SHA-256 checksums.
        
    Raises:
        FileNotFoundError: If any file in the list does not exist.
    """
    manifest = {}
    for path in file_paths:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Cannot checksum missing file: {p}")
        checksum = compute_sha256(p)
        manifest[str(p)] = checksum

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
    
    return manifest


def verify_checksums(
    file_paths: List[Union[str, Path]], 
    expected_checksums: Dict[str, str]
) -> Dict[str, Tuple[bool, str]]:
    """
    Verify that files match their expected checksums.
    
    Args:
        file_paths: List of files to verify.
        expected_checksums: Dictionary mapping file path strings to expected hex checksums.
        
    Returns:
        Dictionary mapping file path to (is_valid: bool, message: str).
    """
    results = {}
    for path in file_paths:
        p_str = str(path)
        if p_str not in expected_checksums:
            results[p_str] = (False, "No expected checksum provided")
            continue
        
        try:
            actual = compute_sha256(path)
            expected = expected_checksums[p_str]
            if actual == expected:
                results[p_str] = (True, "Checksum valid")
            else:
                results[p_str] = (False, f"Checksum mismatch: {actual} != {expected}")
        except FileNotFoundError:
            results[p_str] = (False, "File not found")
        except Exception as e:
            results[p_str] = (False, f"Error reading file: {str(e)}")
    
    return results


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Path to the directory.
        
    Returns:
        The Path object of the directory.
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p
