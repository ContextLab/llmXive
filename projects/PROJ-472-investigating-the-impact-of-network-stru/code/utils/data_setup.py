import os
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional
from config import get_data_root

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_checksums(checksum_file: Path) -> Dict[str, str]:
    """Load checksums from a JSON file."""
    if not checksum_file.exists():
        return {}
    with open(checksum_file, "r") as f:
        return json.load(f)

def save_checksums(checksums: Dict[str, str], checksum_file: Path):
    """Save checksums to a JSON file."""
    with open(checksum_file, "w") as f:
        json.dump(checksums, f, indent=2)

def update_checksum_for_file(file_path: Path, checksums: Dict[str, str]) -> Dict[str, str]:
    """Update the checksum for a specific file in the dictionary."""
    if file_path.exists():
        checksums[file_path.name] = compute_file_checksum(file_path)
    return checksums

def verify_file_integrity(file_path: Path, expected_hash: str) -> bool:
    """Verify if a file's hash matches the expected hash."""
    if not file_path.exists():
        return False
    actual_hash = compute_file_checksum(file_path)
    return actual_hash == expected_hash

def setup_data_environment():
    """
    Setup the data environment:
    1. Ensure directories exist.
    2. Verify the HCP-MMP file and calculate its hash if needed.
    3. Update config.py with the correct hash if it's a placeholder.
    """
    data_root = get_data_root()
    checksum_file = data_root / "checksums.json"
    
    # Ensure directories
    from config import ensure_directories
    ensure_directories()
    
    # Check HCP-MMP file
    from config import HCP_MMP_FILE_PATH, HCP_MMP_HASH
    hcp_file_path = data_root / HCP_MMP_FILE_PATH
    
    if hcp_file_path.exists():
        current_hash = compute_file_checksum(hcp_file_path)
        if HCP_MMP_HASH == "0" * 64:
            # If placeholder, update the config (this would require editing the file)
            # For now, we just log it. The user must update config.py manually or via a script.
            print(f"WARNING: HCP_MMP_HASH in config.py is a placeholder. "
                  f"Actual hash of {hcp_file_path} is: {current_hash}")
            print("Please update config.py with the correct hash.")
        else:
            if current_hash == HCP_MMP_HASH:
                print(f"HCP-MMP file verified: {hcp_file_path}")
            else:
                print(f"ERROR: HCP-MMP file hash mismatch. "
                      f"Expected: {HCP_MMP_HASH}, Got: {current_hash}")
    else:
        print(f"WARNING: HCP-MMP file not found at {hcp_file_path}. "
              "Please place the file in data/raw as per T004.")
    
    # Load/Save checksums
    checksums = load_checksums(checksum_file)
    if hcp_file_path.exists():
        checksums = update_checksum_for_file(hcp_file_path, checksums)
        save_checksums(checksums, checksum_file)
