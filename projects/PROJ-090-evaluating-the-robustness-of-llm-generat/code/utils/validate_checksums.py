"""
Checksum validation script for verifying data directory integrity.

This script generates and verifies SHA-256 checksums for files within the
`data/` directory structure. It supports two modes:
1. `generate`: Creates a `.checksums` manifest file for all non-hidden files.
2. `verify`: Compares current file hashes against the manifest to detect corruption.
"""

import hashlib
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Project root is the parent of the `code` directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CHECKSUM_MANIFEST = DATA_DIR / ".checksums.txt"

def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """Compute the hash of a file in chunks to handle large files."""
    hasher = hashlib.new(algorithm)
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (IOError, OSError) as e:
        raise RuntimeError(f"Failed to read file {file_path}: {e}")

def get_data_files(root_dir: Path) -> List[Path]:
    """
    Recursively get all non-hidden files in the data directory.
    Excludes hidden files (starting with '.') and the checksum manifest itself.
    """
    files = []
    if not root_dir.exists():
        return files

    for file_path in root_dir.rglob("*"):
        if file_path.is_file():
            # Skip hidden files and the manifest itself
            if file_path.name.startswith(".") or file_path == CHECKSUM_MANIFEST:
                continue
            files.append(file_path)
    return sorted(files)

def generate_checksums() -> Tuple[int, int]:
    """
    Generate checksums for all files in data/ and write to manifest.
    Returns (total_files, success_count).
    """
    if not DATA_DIR.exists():
        print(f"Error: Data directory not found at {DATA_DIR}")
        return 0, 0

    files = get_data_files(DATA_DIR)
    if not files:
        print("No files found to checksum in data/.")
        return 0, 0

    print(f"Generating checksums for {len(files)} files...")
    manifest_lines = []

    for file_path in files:
        try:
            rel_path = file_path.relative_to(DATA_DIR)
            file_hash = compute_file_hash(file_path)
            manifest_lines.append(f"{file_hash}  {rel_path}")
            print(f"  [OK] {rel_path}")
        except Exception as e:
            print(f"  [ERROR] {file_path}: {e}")

    try:
        with open(CHECKSUM_MANIFEST, "w", encoding="utf-8") as f:
            f.write("\n".join(manifest_lines) + "\n")
        print(f"\nManifest written to: {CHECKSUM_MANIFEST}")
        return len(files), len(manifest_lines)
    except IOError as e:
        print(f"Failed to write manifest: {e}")
        return len(files), 0

def verify_checksums() -> Tuple[int, int, List[str]]:
    """
    Verify current files against the stored checksums.
    Returns (total_checked, passed_count, list_of_failed_files).
    """
    if not CHECKSUM_MANIFEST.exists():
        print(f"Error: Checksum manifest not found at {CHECKSUM_MANIFEST}")
        print("Run with --generate first to create the manifest.")
        return 0, 0, []

    if not DATA_DIR.exists():
        print(f"Error: Data directory not found at {DATA_DIR}")
        return 0, 0, []

    # Load stored checksums
    stored_checksums: Dict[Path, str] = {}
    try:
        with open(CHECKSUM_MANIFEST, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split("  ", 1)
                if len(parts) != 2:
                    continue
                hash_val, rel_path = parts
                stored_checksums[Path(rel_path)] = hash_val
    except IOError as e:
        print(f"Failed to read manifest: {e}")
        return 0, 0, []

    if not stored_checksums:
        print("Manifest is empty.")
        return 0, 0, []

    print(f"Verifying {len(stored_checksums)} files against manifest...")
    passed = 0
    failed_files: List[str] = []

    for rel_path, expected_hash in stored_checksums.items():
        full_path = DATA_DIR / rel_path
        if not full_path.exists():
            print(f"  [MISSING] {rel_path}")
            failed_files.append(str(rel_path))
            continue

        try:
            current_hash = compute_file_hash(full_path)
            if current_hash == expected_hash:
                passed += 1
                # print(f"  [OK] {rel_path}")
            else:
                print(f"  [MISMATCH] {rel_path}")
                print(f"    Expected: {expected_hash}")
                print(f"    Got:      {current_hash}")
                failed_files.append(str(rel_path))
        except Exception as e:
            print(f"  [ERROR] {rel_path}: {e}")
            failed_files.append(str(rel_path))

    print(f"\nVerification complete: {passed}/{len(stored_checksums)} passed.")
    if failed_files:
        print(f"Failed files: {', '.join(failed_files)}")
    else:
        print("All files verified successfully.")

    return len(stored_checksums), passed, failed_files

def main() -> int:
    """Main entry point for CLI."""
    if len(sys.argv) < 2:
        print("Usage: python -m code.utils.validate_checksums <generate|verify>")
        return 1

    mode = sys.argv[1].lower()

    if mode == "generate":
        total, success = generate_checksums()
        return 0 if success == total else 1
    elif mode == "verify":
        total, passed, failed = verify_checksums()
        return 0 if not failed else 1
    else:
        print(f"Unknown mode: {mode}. Use 'generate' or 'verify'.")
        return 1

if __name__ == "__main__":
    sys.exit(main())