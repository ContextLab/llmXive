import os
import sys
import hashlib
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any

# Import Config directly to access attributes dynamically
from config import Config

# Determine manifest path dynamically based on actual Config attributes
# The Config class is accessed via attribute names that may vary
config = Config()

# Attempt to resolve DATA_RAW or fallback to standard paths
data_raw_path = None
if hasattr(config, 'DATA_RAW'):
    data_raw_path = config.DATA_RAW
elif hasattr(config, 'DATA_DIR') and hasattr(config, 'DATA_RAW_SUBDIR'):
    data_raw_path = getattr(config, 'DATA_DIR') / getattr(config, 'DATA_RAW_SUBDIR')
elif hasattr(config, 'DATA_DIR'):
    # Fallback: assume data_raw is a subdirectory of DATA_DIR
    data_raw_path = getattr(config, 'DATA_DIR') / 'raw'
else:
    # Fallback to standard project structure if attributes are missing
    data_raw_path = Path("data/raw")

# The manifest is generated in data/raw/ by T006 as sampled_manifest.json
# We look there first. If not found, we look in data/ as a fallback.
MANIFEST_PATH = data_raw_path / "sampled_manifest.json"
if not MANIFEST_PATH.exists():
    # Check if it exists in data/ as a fallback for legacy paths
    fallback_manifest = Path("data") / "sampled_manifest.json"
    if fallback_manifest.exists():
        MANIFEST_PATH = fallback_manifest

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        raise RuntimeError(f"Failed to compute hash for {file_path}: {e}")

def load_manifest() -> List[Dict[str, str]]:
    """Load the sampled_manifest.json file."""
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(
            f"Manifest not found at {MANIFEST_PATH}. "
            "Please ensure T006 (download.py) has run successfully and generated data/raw/sampled_manifest.json."
        )
    with open(MANIFEST_PATH, "r") as f:
        data = json.load(f)
        # Expected format is a list of objects: [{"file": "<filename>", "sha256": "<hash>"}]
        if not isinstance(data, list):
            raise ValueError(f"Manifest at {MANIFEST_PATH} must be a JSON list.")
        if len(data) == 0:
            raise ValueError(f"Manifest at {MANIFEST_PATH} is empty.")
        for item in data:
            if 'file' not in item or 'sha256' not in item:
                raise ValueError(f"Manifest item missing 'file' or 'sha256': {item}")
        return data

def verify_directory_integrity(directory: Path, manifest: Optional[List[Dict[str, str]]] = None) -> bool:
    """
    Verify SHA-256 checksums of all files in directory against manifest.
    Returns True if all match, False otherwise.
    """
    if manifest is None:
        manifest = load_manifest()

    all_valid = True
    files_checked = 0
    
    # We only verify files that are in the manifest and exist in the directory
    for item in manifest:
        filename = item['file']
        expected_hash = item['sha256']
        
        # Try relative to directory first, then absolute
        file_path = directory / filename
        if not file_path.exists():
            # Try just the filename in case it's in the current dir
            if Path(filename).exists():
                file_path = Path(filename)
            else:
                print(f"Missing file: {filename} (expected in {directory})")
                all_valid = False
                continue
        
        actual_hash = compute_sha256(file_path)
        if actual_hash != expected_hash:
            print(f"Checksum mismatch for {filename}: expected {expected_hash}, got {actual_hash}")
            all_valid = False
        else:
            print(f"Verified: {filename}")
            files_checked += 1

    if files_checked == 0:
        print(f"Warning: No files from manifest found in {directory}.")
        # This is a failure condition for the gate: we expected to verify files
        return False

    return all_valid

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Verify directory checksums against manifest (T006a)")
    parser.add_argument("--directory", type=str, default=str(data_raw_path), 
                      help="Directory to verify (default: data/raw)")
    args = parser.parse_args()

    directory = Path(args.directory)
    if not directory.exists():
        print(f"Error: Directory {directory} does not exist.")
        sys.exit(1)

    try:
        if verify_directory_integrity(directory):
            print("Verification successful: All checksums match.")
            sys.exit(0)
        else:
            print("Verification failed: Checksum mismatches or missing files detected.")
            sys.exit(1)
    except FileNotFoundError as e:
        print(f"Verification error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Verification error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Verification error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()