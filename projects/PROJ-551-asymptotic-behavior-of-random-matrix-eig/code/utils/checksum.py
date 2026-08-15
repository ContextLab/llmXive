"""
Checksum utilities for data hygiene and integrity verification.

Implements Constitution Principle III: Data Hygiene.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Union, Optional

from .config import get_project_paths


def compute_file_checksum(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        Hexadecimal string of the checksum.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    hasher = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
            
    return hasher.hexdigest()


def compute_directory_checksums(dir_path: Union[str, Path], pattern: str = "*") -> Dict[str, str]:
    """
    Compute checksums for all files in a directory matching a pattern.
    
    Args:
        dir_path: Path to the directory.
        pattern: Glob pattern to match files (default: "*").
        
    Returns:
        Dictionary mapping relative file paths to their checksums.
    """
    dir_path = Path(dir_path)
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {dir_path}")
        
    checksums = {}
    
    for file_path in dir_path.glob(pattern):
        if file_path.is_file():
            rel_path = file_path.relative_to(dir_path)
            checksums[str(rel_path)] = compute_file_checksum(file_path)
            
    return checksums


def save_checksum_manifest(checksums_list: List[Dict[str, str]], manifest_path: Union[str, Path]) -> None:
    """
    Save a manifest of checksums to a JSON file.
    
    Args:
        checksums_list: List of dictionaries containing checksum information.
        manifest_path: Path where the manifest will be saved.
    """
    manifest_path = Path(manifest_path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    manifest = {
        "checksums": checksums_list,
        "algorithm": "sha256"
    }
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)


def load_checksum_manifest(manifest_path: Union[str, Path]) -> Dict:
    """
    Load a checksum manifest from a JSON file.
    
    Args:
        manifest_path: Path to the manifest file.
        
    Returns:
        Dictionary containing the manifest data.
    """
    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
        
    with open(manifest_path, 'r') as f:
        return json.load(f)


def verify_checksums(manifest_path: Union[str, Path], base_dir: Optional[Union[str, Path]] = None) -> Dict[str, bool]:
    """
    Verify file checksums against a manifest.
    
    Args:
        manifest_path: Path to the checksum manifest.
        base_dir: Base directory for relative paths in the manifest.
        
    Returns:
        Dictionary mapping file paths to verification status (True/False).
    """
    manifest = load_checksum_manifest(manifest_path)
    results = {}
    
    base_dir = Path(base_dir) if base_dir else Path(manifest_path).parent
    
    for checksum_info in manifest.get("checksums", []):
        for file_path_str, expected_checksum in checksum_info.items():
            file_path = base_dir / file_path_str if not Path(file_path_str).is_absolute() else Path(file_path_str)
            
            if not file_path.exists():
                results[file_path_str] = False
                continue
                
            actual_checksum = compute_file_checksum(file_path)
            results[file_path_str] = (actual_checksum == expected_checksum)
            
    return results
