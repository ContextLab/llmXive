"""
Checksum utility module for data integrity verification.

This module provides functions to generate and verify SHA-256 checksums
for data files, ensuring data integrity as per Constitution Principle III.
"""
import hashlib
import os
from pathlib import Path
from typing import Optional

def generate_checksum(file_path: str, block_size: int = 65536) -> str:
    """
    Generates a SHA-256 checksum for the specified file.
    
    Args:
        file_path: Path to the file to checksum.
        block_size: Size of blocks to read (default 64KB).
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            sha256_hash.update(block)
    
    return sha256_hash.hexdigest()

def save_checksum(file_path: str, checksum_path: str) -> None:
    """
    Generates a checksum for a file and saves it to a .sha256 file.
    
    Args:
        file_path: Path to the file to checksum.
        checksum_path: Path where the checksum file will be saved.
    """
    checksum = generate_checksum(file_path)
    checksum_file = Path(checksum_path)
    checksum_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Format: <checksum>  <filename>
    filename = os.path.basename(file_path)
    with open(checksum_file, "w") as f:
        f.write(f"{checksum}  {filename}\n")
    
    return checksum

def verify_checksum(file_path: str, checksum_path: Optional[str] = None) -> bool:
    """
    Verifies a file against its SHA-256 checksum.
    
    Args:
        file_path: Path to the file to verify.
        checksum_path: Optional path to the .sha256 file. If not provided,
                       looks for <file_path>.sha256.
        
    Returns:
        True if the checksum matches, False otherwise.
        
    Raises:
        FileNotFoundError: If the file or checksum file does not exist.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if checksum_path is None:
        checksum_path = str(file_path) + ".sha256"
    
    checksum_file = Path(checksum_path)
    if not checksum_file.exists():
        raise FileNotFoundError(f"Checksum file not found: {checksum_file}")
    
    # Read expected checksum from file
    with open(checksum_file, "r") as f:
        line = f.read().strip()
        # Format: <checksum>  <filename>
        expected_checksum = line.split()[0]
    
    # Generate actual checksum
    actual_checksum = generate_checksum(str(file_path))
    
    return actual_checksum == expected_checksum

def main():
    """Main entry point for standalone execution (for testing)."""
    import sys
    if len(sys.argv) < 2:
        print("Usage: python checksums.py <file_path> [checksum_path]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    checksum_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        if checksum_path:
            checksum = save_checksum(file_path, checksum_path)
            print(f"Checksum saved to {checksum_path}: {checksum}")
        else:
            checksum = generate_checksum(file_path)
            print(f"Checksum for {file_path}: {checksum}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
