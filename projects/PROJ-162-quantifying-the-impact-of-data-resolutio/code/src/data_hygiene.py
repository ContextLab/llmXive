"""
Data Hygiene Module for llmXive Pipeline.
Implements SHA256 checksum generation, validation, and state management.
"""
import hashlib
import json
import os
import fcntl
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

from src.config import get_data_path, ensure_directories

STATE_DIR = Path("state")
CHECKSUM_FILE = STATE_DIR / "checksums.json"


class StateLock:
    """Context manager for file locking to prevent concurrent writes to state files."""
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.lock_file = None

    def __enter__(self):
        ensure_directories()
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_file = open(self.file_path, 'a+')
        fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX)
        return self.file_path

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.lock_file:
            fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
            self.lock_file.close()
        return False


def calculate_sha256(file_path: Path) -> str:
    """
    Calculate SHA256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files without excessive memory usage
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        raise RuntimeError(f"Error hashing file {file_path}: {e}")


def load_checksums() -> Dict[str, str]:
    """
    Load existing checksums from the state file.
    
    Returns:
        Dictionary mapping file paths to their SHA256 hashes.
        Returns an empty dict if the file does not exist or is empty.
    """
    if not CHECKSUM_FILE.exists():
        return {}
    
    try:
        with open(CHECKSUM_FILE, 'r') as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {}
            return data
    except (json.JSONDecodeError, IOError):
        return {}


def save_checksums(checksums: Dict[str, str]) -> None:
    """
    Save checksums to the state file.
    
    Args:
        checksums: Dictionary mapping file paths to SHA256 hashes.
    """
    ensure_directories()
    CHECKSUM_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with StateLock(CHECKSUM_FILE):
        with open(CHECKSUM_FILE, 'w') as f:
            json.dump(checksums, f, indent=2)


def update_checksum(file_path: Path, checksums: Dict[str, str]) -> Dict[str, str]:
    """
    Update the checksum for a specific file in the dictionary.
    
    Args:
        file_path: Path to the file.
        checksums: Current dictionary of checksums.
        
    Returns:
        Updated dictionary.
    """
    if file_path.exists():
        checksums[str(file_path)] = calculate_sha256(file_path)
    else:
        # Remove if file no longer exists
        checksums.pop(str(file_path), None)
    return checksums


def verify_checksum(file_path: Path, expected_hash: str) -> bool:
    """
    Verify a file's checksum against an expected hash.
    
    Args:
        file_path: Path to the file.
        expected_hash: Expected SHA256 hash.
        
    Returns:
        True if the hash matches, False otherwise.
    """
    if not file_path.exists():
        return False
    
    try:
        actual_hash = calculate_sha256(file_path)
        return actual_hash == expected_hash
    except Exception:
        return False


def verify_all_checksums() -> Dict[str, bool]:
    """
    Verify all files in the state file against their stored checksums.
    
    Returns:
        Dictionary mapping file paths to verification status (True/False).
    """
    checksums = load_checksums()
    results = {}
    
    for file_path_str, expected_hash in checksums.items():
        file_path = Path(file_path_str)
        results[file_path_str] = verify_checksum(file_path, expected_hash)
        
    return results


def clean_state_file() -> None:
    """Remove the checksums state file."""
    if CHECKSUM_FILE.exists():
        CHECKSUM_FILE.unlink()


def get_state_summary() -> Dict[str, Any]:
    """
    Get a summary of the current state.
    
    Returns:
        Dictionary with summary statistics.
    """
    checksums = load_checksums()
    return {
        "total_files": len(checksums),
        "last_updated": time.time(),
        "file_paths": list(checksums.keys())
    }


def generate_all_checksums() -> Dict[str, str]:
    """
    Scan the data directory and generate checksums for all files.
    
    Returns:
        Dictionary mapping relative file paths to SHA256 hashes.
    """
    data_path = get_data_path()
    checksums = {}
    
    if not data_path.exists():
        return checksums
        
    for root, _, files in os.walk(data_path):
        for file in files:
            file_path = Path(root) / file
            # Store relative path from project root for portability
            rel_path = file_path.relative_to(Path.cwd())
            try:
                checksums[str(rel_path)] = calculate_sha256(file_path)
            except Exception:
                # Skip files that cannot be read
                continue
                
    return checksums


def main() -> None:
    """
    CLI entry point to generate checksums for all files in data/
    and write them to state/checksums.json.
    """
    print("Generating SHA256 checksums for all files in data/...")
    checksums = generate_all_checksums()
    
    if not checksums:
        print("No files found in data/ directory.")
        # Write empty dict to state file to indicate scan occurred
        save_checksums({})
        return
        
    save_checksums(checksums)
    print(f"Checksums saved to {CHECKSUM_FILE}")
    print(f"Total files processed: {len(checksums)}")


if __name__ == "__main__":
    main()