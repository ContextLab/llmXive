"""
utils/checksum.py

Generates SHA-256 checksums for all files in the `data/processed/` directory.
Implements Constitution Principle III: Data Integrity via Cryptographic Hashing.

This script must be run to generate `results/checksums.json` which serves as
the manifest for data verification.
"""
import os
import sys
import hashlib
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any

# Project root resolution (assumed to be run from project root or via python -m)
# We look for 'data/processed' relative to the current working directory
DEFAULT_INPUT_DIR = "data/processed"
DEFAULT_OUTPUT_FILE = "results/checksums.json"

def calculate_sha256(file_path: Path) -> str:
    """
    Calculates the SHA-256 hash of a file.
    Reads in chunks to handle large files efficiently.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise RuntimeError(f"Failed to read file {file_path}: {e}")

def generate_checksums(input_dir: str, output_file: str) -> Dict[str, Any]:
    """
    Walks the input directory, calculates SHA-256 for every file,
    and writes the manifest to the output file.
    """
    input_path = Path(input_dir)
    output_path = Path(output_file)

    if not input_path.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
    
    if not input_path.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {input_dir}")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    checksums: Dict[str, str] = {}
    processed_count = 0

    # Walk recursively to catch all files
    for root, _, files in os.walk(input_path):
        for filename in files:
            # Skip hidden files or temp files if necessary, but generally hash everything
            file_path = Path(root) / filename
            
            # Calculate relative path from the input directory for the manifest
            relative_path = file_path.relative_to(input_path)
            
            try:
                file_hash = calculate_sha256(file_path)
                checksums[str(relative_path)] = file_hash
                processed_count += 1
                print(f"  Hashed: {relative_path}")
            except RuntimeError as e:
                print(f"  Warning: Skipping {relative_path} due to error: {e}", file=sys.stderr)

    manifest = {
        "algorithm": "SHA-256",
        "base_directory": str(input_path.absolute()),
        "file_count": processed_count,
        "checksums": checksums
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nChecksum generation complete.")
    print(f"Processed {processed_count} files.")
    print(f"Manifest written to: {output_path}")

    return manifest

def main():
    parser = argparse.ArgumentParser(
        description="Generate SHA-256 checksums for data/processed/ directory."
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default=DEFAULT_INPUT_DIR,
        help=f"Directory to scan for files (default: {DEFAULT_INPUT_DIR})"
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default=DEFAULT_OUTPUT_FILE,
        help=f"Output JSON manifest file (default: {DEFAULT_OUTPUT_FILE})"
    )

    args = parser.parse_args()

    try:
        generate_checksums(args.input_dir, args.output_file)
        sys.exit(0)
    except (FileNotFoundError, NotADirectoryError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()