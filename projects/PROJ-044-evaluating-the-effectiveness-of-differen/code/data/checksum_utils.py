"""
Checksumming and verification utility for data integrity.

This module provides functions to generate SHA-256 checksums for files
and verify existing checksums against file contents.
"""

import hashlib
import os
from pathlib import Path
from typing import Optional

CHUNK_SIZE = 8192  # 8KB chunks for reading large files


def compute_sha256(file_path: str, chunk_size: int = CHUNK_SIZE) -> str:
    """
    Compute the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to checksum.
        chunk_size: Size of chunks to read at a time.
        
    Returns:
        Hexadecimal SHA-256 hash string.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file path is invalid.
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
    
    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()


def generate_checksum_file(file_path: str, output_path: Optional[str] = None) -> str:
    """
    Generate a SHA-256 checksum file for a given file.
    
    Args:
        file_path: Path to the file to checksum.
        output_path: Optional path for the checksum file. If None, 
                    creates <file_path>.sha256 in the same directory.
                    
    Returns:
        Path to the generated checksum file.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the input path is not a file.
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
    
    checksum = compute_sha256(file_path)
    
    if output_path is None:
        output_path = str(file_path.with_suffix(file_path.suffix + ".sha256"))
    
    output_file = Path(output_path)
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write checksum file in standard format: <hash>  <filename>
    with open(output_file, "w") as f:
        f.write(f"{checksum}  {file_path.name}\n")
    
    return str(output_file)


def verify_checksum(file_path: str, checksum_file_path: Optional[str] = None) -> bool:
    """
    Verify a file's checksum against a stored checksum file.
    
    Args:
        file_path: Path to the file to verify.
        checksum_file_path: Optional path to the checksum file. If None, 
                           looks for <file_path>.sha256 in the same directory.
                           
    Returns:
        True if the checksum matches, False otherwise.
        
    Raises:
        FileNotFoundError: If the file or checksum file does not exist.
        ValueError: If the checksum file format is invalid.
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
    
    if checksum_file_path is None:
        checksum_file_path = str(file_path.with_suffix(file_path.suffix + ".sha256"))
    
    checksum_file = Path(checksum_file_path)
    
    if not checksum_file.exists():
        raise FileNotFoundError(f"Checksum file not found: {checksum_file}")
    
    # Read the stored checksum
    with open(checksum_file, "r") as f:
        line = f.readline().strip()
    
    if not line:
        raise ValueError(f"Empty checksum file: {checksum_file}")
    
    # Parse standard format: <hash>  <filename> or just <hash>
    parts = line.split()
    if len(parts) >= 1:
        stored_checksum = parts[0]
    else:
        raise ValueError(f"Invalid checksum format in {checksum_file}")
    
    # Compute current checksum
    current_checksum = compute_sha256(file_path)
    
    return current_checksum == stored_checksum


def batch_verify_checksums(file_paths: list[str]) -> dict[str, bool]:
    """
    Verify checksums for multiple files.
    
    Args:
        file_paths: List of file paths to verify.
        
    Returns:
        Dictionary mapping file paths to verification results.
    """
    results = {}
    
    for file_path in file_paths:
        try:
            results[file_path] = verify_checksum(file_path)
        except (FileNotFoundError, ValueError) as e:
            results[file_path] = False
            print(f"Warning: {e}")
    
    return results
