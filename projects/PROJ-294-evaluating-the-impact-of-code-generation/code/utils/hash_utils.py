import hashlib
import os
from utils import compute_sha256, verify_checksum

def hash_file(file_path: str) -> str:
    """Compute SHA256 hash of a file."""
    return compute_sha256(file_path)

def verify_file_hash(file_path: str, expected_hash: str) -> bool:
    """Verify file hash against expected value."""
    return verify_checksum(file_path, expected_hash)

def main():
    """Utility entry point."""
    pass

if __name__ == "__main__":
    main()
