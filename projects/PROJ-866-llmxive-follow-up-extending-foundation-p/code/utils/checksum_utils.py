"""
Checksum utilities for llmXive pipeline.

This module provides functions for computing SHA-256 hashes of files and directories.
"""
import hashlib
import os
from pathlib import Path
from typing import Dict, Optional


def compute_sha256_file(file_path: str) -> str:
    """
    Compute SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Hexadecimal SHA-256 hash string
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def compute_sha256_string(data: str) -> str:
    """
    Compute SHA-256 hash of a string.
    
    Args:
        data: String to hash
        
    Returns:
        Hexadecimal SHA-256 hash string
    """
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def compute_directory_hash(directory_path: str) -> str:
    """
    Compute a combined SHA-256 hash of all files in a directory.
    
    The hash is computed by:
    1. Sorting all files recursively
    2. Computing individual file hashes
    3. Combining them in sorted order
    
    Args:
        directory_path: Path to the directory
        
    Returns:
        Hexadecimal SHA-256 hash of the directory contents
    """
    directory = Path(directory_path)
    if not directory.exists():
        return hashlib.sha256(b"").hexdigest()
    
    # Get all files sorted by relative path
    files = []
    for file_path in sorted(directory.rglob('*')):
        if file_path.is_file():
            relative_path = file_path.relative_to(directory)
            files.append((str(relative_path), file_path))
    
    if not files:
        return hashlib.sha256(b"").hexdigest()
    
    # Compute combined hash
    combined_hash = hashlib.sha256()
    for rel_path, file_path in files:
        # Include relative path in hash
        combined_hash.update(rel_path.encode('utf-8'))
        # Include file hash
        file_hash = compute_sha256_file(str(file_path))
        combined_hash.update(file_hash.encode('utf-8'))
    
    return combined_hash.hexdigest()


def main():
    """Command-line interface for checksum utilities."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Checksum utilities')
    parser.add_argument('--file', type=str, help='Compute hash of a file')
    parser.add_argument('--directory', type=str, help='Compute hash of a directory')
    parser.add_argument('--string', type=str, help='Compute hash of a string')
    
    args = parser.parse_args()
    
    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: File not found: {args.file}")
            return 1
        hash_val = compute_sha256_file(args.file)
        print(f"{hash_val}  {args.file}")
        return 0
    
    elif args.directory:
        if not os.path.exists(args.directory):
            print(f"Error: Directory not found: {args.directory}")
            return 1
        hash_val = compute_directory_hash(args.directory)
        print(f"{hash_val}  {args.directory}/")
        return 0
    
    elif args.string:
        hash_val = compute_sha256_string(args.string)
        print(hash_val)
        return 0
    
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    exit(main())
