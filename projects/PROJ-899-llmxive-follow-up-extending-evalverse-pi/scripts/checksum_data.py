"""
Script to verify data checksums.
"""
import os
import sys
import hashlib
from pathlib import Path
import json
from src.data.download import compute_sha256, load_stored_checksum, save_checksum

def main():
    """Main entry point for checksum verification."""
    from src.data.config import get_raw_data_path, get_state_path
    
    raw_dir = get_raw_data_path()
    state_dir = get_state_path()
    
    if not raw_dir.exists():
        print(f"Data directory not found: {raw_dir}")
        sys.exit(1)
    
    # Calculate checksums for all files
    checksums = {}
    for file_path in raw_dir.rglob("*"):
        if file_path.is_file():
          rel_path = file_path.relative_to(raw_dir)
          checksums[str(rel_path)] = compute_sha256(file_path)
    
    # Save checksums
    checksum_file = state_dir / "data_checksums.json"
    with open(checksum_file, "w") as f:
        json.dump(checksums, f, indent=2)
    
    print(f"Checksums saved to {checksum_file}")
    print(f"Total files processed: {len(checksums)}")

if __name__ == "__main__":
    main()
