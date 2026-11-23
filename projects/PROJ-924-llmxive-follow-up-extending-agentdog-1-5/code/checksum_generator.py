"""
Checksum Generator for Raw Data Integrity Tracking.

This script computes SHA-256 checksums for all files in the data/raw/ directory
and saves them to data/checksums.json for integrity verification.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any

from config import get_path, ensure_directories


def compute_file_checksum(file_path: Path) -> str:
    """
    Compute SHA-256 checksum of a file.

    Args:
        file_path: Path to the file to checksum.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def generate_checksums(raw_dir: Path) -> Dict[str, Any]:
    """
    Generate checksums for all files in the raw data directory.

    Args:
        raw_dir: Path to the raw data directory.

    Returns:
        Dictionary containing checksums and metadata.
    """
    checksums = {
        "version": "1.0",
        "algorithm": "sha256",
        "generated_files": [],
        "file_checksums": {}
    }

    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")

    files_processed = 0
    for file_path in raw_dir.rglob("*"):
        if file_path.is_file():
            relative_path = str(file_path.relative_to(raw_dir))
            checksum = compute_file_checksum(file_path)
            checksums["file_checksums"][relative_path] = checksum
            checksums["generated_files"].append({
                "path": relative_path,
                "checksum": checksum,
                "size_bytes": file_path.stat().st_size
            })
            files_processed += 1

    checksums["total_files"] = files_processed

    return checksums


def save_checksums(checksums: Dict[str, Any], output_path: Path) -> None:
    """
    Save checksums dictionary to a JSON file.

    Args:
        checksums: Dictionary containing checksum data.
        output_path: Path to save the JSON file.
    """
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2, sort_keys=True)


def main() -> None:
    """Main entry point for checksum generation."""
    # Ensure required directories exist
    ensure_directories()

    # Get paths from config
    raw_dir = get_path("raw_data_dir")
    checksums_path = get_path("checksums_file")

    print(f"Scanning raw data directory: {raw_dir}")
    print(f"Output file: {checksums_path}")

    # Generate checksums
    checksums = generate_checksums(raw_dir)

    # Save to file
    save_checksums(checksums, checksums_path)

    print(f"Successfully generated checksums for {checksums['total_files']} files.")
    print(f"Checksums saved to: {checksums_path}")


if __name__ == "__main__":
    main()
