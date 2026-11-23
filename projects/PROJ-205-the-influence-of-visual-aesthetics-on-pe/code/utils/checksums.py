"""
Checksum utilities for data integrity verification.

Provides functions to compute, save, and verify SHA-256 checksums for data files.
"""
import os
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any

class FileChecksumError(Exception):
    """Raised when a checksum verification fails."""
    pass

def get_project_root() -> Path:
    """Returns the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def get_checksum_store_path() -> Path:
    """Returns the path to the checksums JSON file."""
    return get_project_root() / "data" / "raw" / ".checksums.json"

def compute_checksum(filepath: str) -> str:
    """
    Computes the SHA-256 checksum of a file.
    
    Args:
        filepath (str): Path to the file.
        
    Returns:
        str: Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_checksums() -> Dict[str, str]:
    """
    Loads the stored checksums from the JSON file.
    
    Returns:
        Dict[str, str]: Dictionary mapping file paths to checksums.
    """
    checksum_path = get_checksum_store_path()
    if not checksum_path.exists():
        return {}
    
    with open(checksum_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_checksums(data: Dict[str, str], filepath: Optional[str] = None) -> None:
    """
    Saves the checksums to the JSON file.
    
    Args:
        data (Dict[str, str]): Dictionary of file paths to checksums.
        filepath (Optional[str]): Optional specific path to write to.
    """
    target_path = Path(filepath) if filepath else get_checksum_store_path()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing checksums to merge
    existing = load_checksums()
    existing.update(data)
    
    with open(target_path, 'w', encoding='utf-8') as f:
        json.dump(existing, f, indent=2)

def verify_checksum(filepath: str, expected_hash: Optional[str] = None) -> bool:
    """
    Verifies the checksum of a file against the stored value.
    
    Args:
        filepath (str): Path to the file to verify.
        expected_hash (Optional[str]): If provided, verifies against this hash.
                                       Otherwise, uses the stored hash.
                                       
    Returns:
        bool: True if verification passes.
        
    Raises:
        FileChecksumError: If verification fails.
        FileNotFoundError: If the file or stored checksums are missing.
    """
    abs_path = str(Path(filepath).resolve())
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found for checksum verification: {filepath}")
    
    if expected_hash is None:
        stored_checksums = load_checksums()
        if abs_path not in stored_checksums:
            # Check if relative path is stored
            rel_path = str(Path(filepath).relative_to(get_project_root()))
            if rel_path not in stored_checksums:
                raise FileNotFoundError(f"No stored checksum found for: {filepath}")
            expected_hash = stored_checksums[rel_path]
        else:
            expected_hash = stored_checksums[abs_path]
    
    current_hash = compute_checksum(filepath)
    
    if current_hash != expected_hash:
        raise FileChecksumError(
            f"Checksum mismatch for {filepath}. "
            f"Expected: {expected_hash}, Got: {current_hash}"
        )
    
    return True

def verify_submissions_integrity() -> bool:
    """
    Convenience function to verify the main submissions file.
    
    Returns:
        bool: True if valid.
    """
    from utils.helpers import get_submissions_csv_path
    return verify_checksum(str(get_submissions_csv_path()))

def main():
    """
    Command line interface for checksum operations.
    Usage:
      python -m utils.checksums --compute <file>
      python -m utils.checksums --verify <file>
    """
    import argparse
    parser = argparse.ArgumentParser(description="Checksum utility")
    parser.add_argument("--compute", type=str, help="Compute checksum for a file")
    parser.add_argument("--verify", type=str, help="Verify checksum for a file")
    
    args = parser.parse_args()
    
    if args.compute:
        h = compute_checksum(args.compute)
        print(f"Checksum for {args.compute}: {h}")
        # Save it
        save_checksums({args.compute: h})
        print("Saved to .checksums.json")
        
    elif args.verify:
        try:
            verify_checksum(args.verify)
            print(f"Checksum verified for {args.verify}")
        except (FileChecksumError, FileNotFoundError) as e:
            print(f"Verification failed: {e}")
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    import sys
    main()
