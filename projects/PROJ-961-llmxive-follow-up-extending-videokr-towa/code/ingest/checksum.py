"""
Checksum utility for verifying data integrity.
"""
import hashlib
import json
import os
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Union


def compute_sha256(file_path: Union[str, Path]) -> str:
    """
    Compute SHA-256 hash of a file.
    
    Args:
        file_path (Union[str, Path]): Path to the file.
        
    Returns:
        str: SHA-256 hash as hexadecimal string.
    """
    sha256_hash = hashlib.sha256()
    path_obj = Path(file_path) if isinstance(file_path, str) else file_path
    
    with open(path_obj, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest()


def verify_raw_data_integrity(
    file_path: Union[str, Path],
    expected_hash: str
) -> bool:
    """
    Verify a file's integrity against an expected hash.
    
    Args:
        file_path (Union[str, Path]): Path to the file.
        expected_hash (str): Expected SHA-256 hash.
        
    Returns:
        bool: True if hash matches, False otherwise.
    """
    actual_hash = compute_sha256(file_path)
    return actual_hash == expected_hash


def generate_checksum_file(
    file_path: Union[str, Path],
    output_path: Union[str, Path]
) -> Dict[str, str]:
    """
    Generate a checksum file for a given file.
    
    Args:
        file_path (Union[str, Path]): Path to the file.
        output_path (Union[str, Path]): Path for the checksum file.
        
    Returns:
        Dict[str, str]: Dictionary with file path and hash.
    """
    file_hash = compute_sha256(file_path)
    checksum_data = {
        "file": str(file_path),
        "hash": file_hash
    }
    
    output_obj = Path(output_path) if isinstance(output_path, str) else output_path
    with open(output_obj, 'w') as f:
        json.dump(checksum_data, f, indent=2)
    
    return checksum_data


def verify_all_raw_data(
    checksum_file_path: Union[str, Path],
    base_dir: Optional[Union[str, Path]] = None
) -> Dict[str, bool]:
    """
    Verify all files listed in a checksum file.
    
    Args:
        checksum_file_path (Union[str, Path]): Path to the checksum file.
        base_dir (Optional[Union[str, Path]]): Base directory for relative paths.
        
    Returns:
        Dict[str, bool]: Dictionary mapping file paths to verification results.
    """
    checksum_obj = Path(checksum_file_path) if isinstance(checksum_file_path, str) else checksum_file_path
    
    with open(checksum_obj, 'r') as f:
        checksum_data = json.load(f)
    
    results: Dict[str, bool] = {}
    base_path = Path(base_dir) if base_dir else Path.cwd()
    
    for item in checksum_data:
        file_path = base_path / item["file"] if not Path(item["file"]).is_absolute() else Path(item["file"])
        expected_hash = item["hash"]
        
        if file_path.exists():
            results[str(file_path)] = verify_raw_data_integrity(file_path, expected_hash)
        else:
            results[str(file_path)] = False
    
    return results


def main() -> None:
    """Main entry point for checksum module."""
    pass


if __name__ == "__main__":
    main()
