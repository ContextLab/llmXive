import os
import sys
import hashlib
from pathlib import Path
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from src.data.download import compute_sha256, load_stored_checksum, save_checksum
from src.config import get_raw_data_dir, get_state_root

def main():
    raw_dir = get_raw_data_dir()
    state_dir = get_state_root()
    
    if not raw_dir.exists():
        print("Raw data directory does not exist.")
        return 1

    checksums = {}
    for root, _, files in os.walk(raw_dir):
        for file in files:
            file_path = Path(root) / file
            checksum = compute_sha256(file_path)
            rel_path = file_path.relative_to(raw_dir)
            checksums[str(rel_path)] = checksum

    output_file = state_dir / "artifact_hashes.json"
    with open(output_file, 'w') as f:
        json.dump(checksums, f, indent=2)
    
    print(f"Checksums saved to {output_file}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
