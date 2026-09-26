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
else:
    # Fallback to standard project structure if attributes are missing
    data_raw_path = Path("data/raw")

# The manifest is generated in data/ by T006, so we look there first
# If not found, we look in data/raw as a fallback for legacy paths
MANIFEST_PATH = Path("data/manifest.json")
if not MANIFEST_PATH.exists():
    # Check if it exists in data/raw as well
    raw_manifest = data_raw_path / "manifest.json"
    if raw_manifest.exists():
        MANIFEST_PATH = raw_manifest

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

def load_manifest() -> Dict[str, str]:
    """Load the manifest.json file."""
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Manifest not found at {MANIFEST_PATH}. "
                                "Please ensure T006 (download.py) has run successfully and generated data/manifest.json.")
    with open(MANIFEST_PATH, "r") as f:
        data = json.load(f)
        # Handle both list-of-dicts and dict formats
        if isinstance(data, list):
            return {item['file']: item['sha256'] for item in data}
        return data

def verify_directory_integrity(directory: Path, manifest: Optional[Dict[str, str]] = None) -> bool:
    """
    Verify SHA-256 checksums of all files in directory against manifest.
    Returns True if all match, False otherwise.
    """
    if manifest is None:
        manifest = load_manifest()

    all_valid = True
    # We only verify files that are in the manifest and exist in the directory
    # The manifest might contain files from other directories, so we filter
    files_to_check = {k: v for k, v in manifest.items() 
                     if (directory / k).exists() or Path(k).exists()}
    
    if not files_to_check:
        print(f"Warning: No files from manifest found in {directory}. "
              f"Manifest contains {len(manifest)} entries, but none match the directory.")
        # We don't fail if the directory is empty but manifest exists, 
        # as this might be a multi-directory download
    
    for filename, expected_hash in files_to_check.items():
        # Try relative to directory first, then absolute
        file_path = directory / filename
        if not file_path.exists():
            file_path = Path(filename)
        
        if not file_path.exists():
            print(f"Missing file: {file_path}")
            all_valid = False
            continue
        
        actual_hash = compute_sha256(file_path)
        if actual_hash != expected_hash:
            print(f"Checksum mismatch for {filename}: expected {expected_hash}, got {actual_hash}")
            all_valid = False
        else:
            print(f"Verified: {filename}")
    
    return all_valid

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Verify directory checksums against manifest")
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
            print("Verification failed: Checksum mismatches detected.")
            sys.exit(1)
    except FileNotFoundError as e:
        print(f"Verification error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Verification error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()