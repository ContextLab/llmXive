"""
Utility script to compute SHA-256 hashes for all files under data/ and write a manifest to state/.

This script ensures data integrity and enforces the constitutional rule that derivations
must be written to new filenames (no in-place modification) by recording checksums.
"""

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add project root to path to ensure imports work regardless of cwd
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
STATE_DIR = PROJECT_ROOT / "state"
MANIFEST_PATH = STATE_DIR / "hash_manifest.json"

def compute_sha256(file_path: Path) -> str:
    """Compute the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except (IOError, OSError) as e:
        raise RuntimeError(f"Failed to read file {file_path}: {e}")

def hash_directory(directory: Path, extensions: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Recursively hash all files in a directory.

    Args:
        directory: Path to the directory to hash.
        extensions: Optional list of file extensions to include (e.g., ['.jsonl', '.json']).
                    If None, all files are included.

    Returns:
        A dictionary mapping relative file paths to their SHA-256 hashes.
    """
    hashes = {}
    if not directory.exists():
        print(f"Warning: Directory {directory} does not exist. Skipping.", file=sys.stderr)
        return hashes

    for root, _, files in os.walk(directory):
        for file in files:
            file_path = Path(root) / file
            rel_path = file_path.relative_to(PROJECT_ROOT)

            if extensions and file_path.suffix not in extensions:
                continue

            try:
                file_hash = compute_sha256(file_path)
                hashes[str(rel_path)] = file_hash
            except RuntimeError as e:
                print(f"Error hashing {file_path}: {e}", file=sys.stderr)

    return hashes

def generate_manifest(hashes: Dict[str, str], directory_name: str) -> Dict[str, Any]:
    """
    Generate a manifest dictionary containing metadata and hashes.

    Args:
        hashes: Dictionary of relative paths to hashes.
        directory_name: Name of the directory being hashed (e.g., 'data').

    Returns:
        A dictionary representing the manifest.
    """
    import datetime
    return {
        "directory": directory_name,
        "timestamp": datetime.datetime.now().isoformat(),
        "algorithm": "sha256",
        "file_count": len(hashes),
        "files": hashes
    }

def verify_manifest(manifest_path: Path) -> bool:
    """
    Verify the integrity of files against a stored manifest.

    Args:
        manifest_path: Path to the manifest JSON file.

    Returns:
        True if all files match the manifest, False otherwise.
    """
    if not manifest_path.exists():
        print(f"Error: Manifest not found at {manifest_path}", file=sys.stderr)
        return False

    try:
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in manifest: {e}", file=sys.stderr)
        return False

    directory_name = manifest.get("directory", "data")
    target_dir = PROJECT_ROOT / directory_name
    if not target_dir.exists():
        print(f"Error: Target directory {target_dir} not found.", file=sys.stderr)
        return False

    all_match = True
    stored_hashes = manifest.get("files", {})

    for rel_path_str, expected_hash in stored_hashes.items():
        file_path = PROJECT_ROOT / rel_path_str
        if not file_path.exists():
            print(f"Mismatch: File {rel_path_str} missing.", file=sys.stderr)
            all_match = False
            continue

        try:
            actual_hash = compute_sha256(file_path)
            if actual_hash != expected_hash:
                print(f"Mismatch: {rel_path_str} (Expected: {expected_hash}, Got: {actual_hash})", file=sys.stderr)
                all_match = False
            else:
                print(f"OK: {rel_path_str}")
        except RuntimeError as e:
            print(f"Error verifying {rel_path_str}: {e}", file=sys.stderr)
            all_match = False

    return all_match

def hash_artifact(file_path: Path) -> str:
    """
    Compute hash for a single artifact.

    Args:
        file_path: Path to the file.

    Returns:
        SHA-256 hash string.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Artifact not found: {file_path}")
    return compute_sha256(file_path)

def main():
    """
    Main entry point for the hash artifacts utility.
    Computes hashes for all files under data/ and writes the manifest to state/.
    """
    # Ensure state directory exists
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    if not DATA_DIR.exists():
        print(f"Error: Data directory {DATA_DIR} does not exist.", file=sys.stderr)
        sys.exit(1)

    print(f"Hashing files in {DATA_DIR}...")
    hashes = hash_directory(DATA_DIR)

    if not hashes:
        print("No files found to hash in data/.", file=sys.stderr)
        sys.exit(0)

    manifest = generate_manifest(hashes, "data")

    # Write manifest
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Manifest written to {MANIFEST_PATH}")
    print(f"Total files hashed: {manifest['file_count']}")

    # Verify immediately after writing (optional but good practice)
    print("Verifying manifest...")
    if verify_manifest(MANIFEST_PATH):
        print("Verification successful.")
    else:
        print("Verification failed.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()