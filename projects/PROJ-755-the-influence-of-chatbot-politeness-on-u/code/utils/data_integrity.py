"""
Utility functions for data integrity checks, checksums, and manifests.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)


def compute_file_checksum(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Compute checksum of a single file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Hex digest of the checksum
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_func = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def compute_directory_checksum(dir_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Compute a combined checksum for all files in a directory.
    
    Args:
        dir_path: Path to the directory
        algorithm: Hash algorithm to use
        
    Returns:
        Combined checksum string
    """
    dir_path = Path(dir_path)
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {dir_path}")
    
    hash_func = hashlib.new(algorithm)
    
    # Sort files for deterministic ordering
    files = sorted(dir_path.rglob("*"))
    
    for file_path in files:
        if file_path.is_file():
            # Include relative path in hash
            rel_path = str(file_path.relative_to(dir_path))
            hash_func.update(rel_path.encode('utf-8'))
            
            # Include file content hash
            file_hash = compute_file_checksum(file_path, algorithm)
            hash_func.update(file_hash.encode('utf-8'))
    
    return hash_func.hexdigest()


def generate_manifest(dir_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Generate a manifest of all files in a directory with metadata.
    
    Args:
        dir_path: Path to the directory
        
    Returns:
        Dictionary containing file metadata
    """
    dir_path = Path(dir_path)
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {dir_path}")
    
    manifest = {
        "directory": str(dir_path),
        "files": [],
        "total_files": 0,
        "total_size_bytes": 0
    }
    
    for file_path in sorted(dir_path.rglob("*")):
        if file_path.is_file():
            stat = file_path.stat()
            file_info = {
                "path": str(file_path.relative_to(dir_path)),
                "size_bytes": stat.st_size,
                "checksum": compute_file_checksum(file_path),
                "modified_time": stat.st_mtime
            }
            manifest["files"].append(file_info)
            manifest["total_files"] += 1
            manifest["total_size_bytes"] += stat.st_size
    
    return manifest


def verify_manifest(manifest_path: Union[str, Path]) -> Dict[str, bool]:
    """
    Verify files against a manifest.
    
    Args:
        manifest_path: Path to the manifest JSON file
        
    Returns:
        Dictionary with verification results per file
    """
    manifest_path = Path(manifest_path)
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    results = {
        "all_valid": True,
        "file_results": {}
    }
    
    dir_path = Path(manifest["directory"])
    
    for file_info in manifest["files"]:
        file_path = dir_path / file_info["path"]
        expected_checksum = file_info["checksum"]
        
        if not file_path.exists():
            results["file_results"][file_info["path"]] = False
            results["all_valid"] = False
            continue
        
        actual_checksum = compute_file_checksum(file_path)
        is_valid = actual_checksum == expected_checksum
        
        results["file_results"][file_info["path"]] = is_valid
        if not is_valid:
            results["all_valid"] = False
    
    return results


def verify_single_file(file_path: Union[str, Path], expected_checksum: str, algorithm: str = "sha256") -> bool:
    """
    Verify a single file against an expected checksum.
    
    Args:
        file_path: Path to the file
        expected_checksum: Expected checksum value
        algorithm: Hash algorithm used
        
    Returns:
        True if checksum matches
    """
    actual_checksum = compute_file_checksum(file_path, algorithm)
    return actual_checksum == expected_checksum