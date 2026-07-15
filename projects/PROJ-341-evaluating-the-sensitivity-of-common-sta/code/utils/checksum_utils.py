import os
import hashlib
import json
from typing import Dict, Optional, List
from datetime import datetime

def compute_file_checksum(filepath: str, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file.
    
    Args:
        filepath: Path to the file
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Hexadecimal checksum string
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    hash_func = hashlib.new(algorithm)
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            hash_func.update(byte_block)
    
    return hash_func.hexdigest()

def verify_checksum(filepath: str, expected_checksum: str, algorithm: str = "sha256") -> bool:
    """
    Verify a file's checksum against an expected value.
    
    Args:
        filepath: Path to the file
        expected_checksum: Expected checksum value
        algorithm: Hash algorithm to use
        
    Returns:
        True if checksum matches, False otherwise
    """
    actual_checksum = compute_file_checksum(filepath, algorithm)
    return actual_checksum == expected_checksum

def scan_directory_for_checksums(directory: str) -> Dict[str, str]:
    """
    Scan a directory and compute checksums for all files.
    
    Args:
        directory: Path to the directory to scan
        
    Returns:
        Dictionary mapping relative file paths to their checksums
    """
    checksums = {}
    for root, _, files in os.walk(directory):
        for file in files:
            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, directory)
            try:
                checksums[rel_path] = compute_file_checksum(filepath)
            except Exception as e:
                print(f"Warning: Could not compute checksum for {filepath}: {e}")
    return checksums

def main():
    """Main function to demonstrate checksum utilities."""
    print("Checksum Utility Module")
    print("-" * 40)
    
    # Example: Checksum of a known file if it exists
    test_file = "data/simulation_metadata.json"
    if os.path.exists(test_file):
        checksum = compute_file_checksum(test_file)
        print(f"Checksum of {test_file}: {checksum}")
    else:
        print(f"File {test_file} not found.")

if __name__ == "__main__":
    main()