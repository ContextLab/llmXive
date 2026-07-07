"""
T007: Implement checksum verification for raw data.

Computes SHA256 hashes of all files in the data/raw/ directory and records them
in data/checksums.txt. This implements Constitution III (data integrity tracking).
"""

import hashlib
import os
import sys
from pathlib import Path
from typing import Optional

# Add project root to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from setup_data_structure import ensure_directory


def compute_sha256(file_path: Path, chunk_size: int = 8192) -> str:
    """
    Compute SHA256 hash of a file in chunks to handle large files efficiently.

    Args:
        file_path: Path to the file to hash
        chunk_size: Size of chunks to read (default 8KB)

    Returns:
        Hexadecimal SHA256 hash string
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def get_raw_data_files(raw_dir: Path) -> list:
    """
    Recursively get all files in the raw data directory.

    Args:
        raw_dir: Path to the raw data directory

    Returns:
        List of file paths
    """
    if not raw_dir.exists():
        print(f"Warning: Raw data directory does not exist: {raw_dir}")
        return []

    files = []
    for root, _, filenames in os.walk(raw_dir):
        for filename in filenames:
            file_path = Path(root) / filename
            # Skip hidden files and common non-data files
            if not filename.startswith('.') and not filename.endswith(('.pyc', '.pyo')):
                files.append(file_path)

    return sorted(files)


def write_checksums(checksums: list, output_path: Path) -> None:
    """
    Write checksums to the output file in a standard format.

    Format: <hash>  <relative_path>

    Args:
        checksums: List of tuples (file_path, hash_value)
        output_path: Path to the output checksum file
    """
    ensure_directory(output_path.parent)
    with open(output_path, "w", encoding="utf-8") as f:
        for file_path, hash_value in checksums:
            # Use relative path from project root for portability
            rel_path = file_path.relative_to(output_path.parent.parent)
            f.write(f"{hash_value}  {rel_path}\n")


def verify_checksums(checksum_file: Path) -> bool:
    """
    Verify existing checksums against current files.

    Args:
        checksum_file: Path to the checksums file

    Returns:
        True if all checksums match, False otherwise
    """
    if not checksum_file.exists():
        print(f"Checksum file not found: {checksum_file}")
        return False

    all_valid = True
    with open(checksum_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split("  ", 1)
            if len(parts) != 2:
                print(f"Invalid checksum line format: {line}")
                all_valid = False
                continue

            expected_hash, rel_path = parts
            file_path = checksum_file.parent.parent / rel_path

            if not file_path.exists():
                print(f"Missing file: {file_path}")
                all_valid = False
                continue

            actual_hash = compute_sha256(file_path)
            if actual_hash != expected_hash:
                print(f"Checksum mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}")
                all_valid = False
            else:
                print(f"OK: {rel_path}")

    return all_valid


def main(mode: str = "compute") -> int:
    """
    Main entry point for checksum verification.

    Args:
        mode: Either "compute" to generate checksums or "verify" to check them

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    project_root = Path(__file__).parent.parent
    raw_dir = project_root / "data" / "raw"
    checksum_file = project_root / "data" / "checksums.txt"

    if mode == "compute":
        print(f"Computing checksums for files in {raw_dir}...")
        files = get_raw_data_files(raw_dir)

        if not files:
            print("No files found to checksum.")
            # Create empty checksum file to indicate directory was checked
            write_checksums([], checksum_file)
            return 0

        checksums = []
        for file_path in files:
            try:
                hash_value = compute_sha256(file_path)
                checksums.append((file_path, hash_value))
                print(f"  Computed: {file_path.relative_to(project_root)}")
            except Exception as e:
                print(f"  Error hashing {file_path}: {e}")
                return 1

        write_checksums(checksums, checksum_file)
        print(f"\nChecksums written to {checksum_file}")
        print(f"Total files processed: {len(checksums)}")
        return 0

    elif mode == "verify":
        print(f"Verifying checksums from {checksum_file}...")
        if verify_checksums(checksum_file):
            print("\nAll checksums verified successfully.")
            return 0
        else:
            print("\nChecksum verification failed.")
            return 1
    else:
        print(f"Unknown mode: {mode}. Use 'compute' or 'verify'.")
        return 1


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Compute or verify SHA256 checksums for raw data files."
    )
    parser.add_argument(
        "mode",
        nargs="?",
        default="compute",
        choices=["compute", "verify"],
        help="Operation mode: compute (default) or verify"
    )

    args = parser.parse_args()
    sys.exit(main(args.mode))
