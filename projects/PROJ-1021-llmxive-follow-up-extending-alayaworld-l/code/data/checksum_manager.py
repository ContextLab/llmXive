"""
Checksum Manager for Data Artifacts.

This module provides utilities to generate, store, and verify checksums
for data artifacts in the `data/` directory. It ensures data integrity
for both real and synthetic artifacts produced by the pipeline.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Project root relative to this file (assuming code/data/ structure)
# We calculate based on the assumption this file is in code/data/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CHECKSUM_FILE = DATA_DIR / ".checksums.json"


def calculate_sha256(file_path: Path) -> str:
    """
    Calculate the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If the path is a directory.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if file_path.is_dir():
        raise IsADirectoryError(f"Cannot hash directory: {file_path}")

    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files (e.g., videos)
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def generate_checksums(pattern: Optional[str] = None) -> Dict[str, str]:
    """
    Generate checksums for all files in the data directory (or a subdirectory).

    Args:
        pattern: Optional glob pattern to filter files (e.g., "*.json", "videos/*").
                 If None, all files in DATA_DIR are processed.

    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes.
    """
    if not DATA_DIR.exists():
        raise FileNotFoundError(f"Data directory not found: {DATA_DIR}")

    checksums = {}

    # Determine which files to process
    if pattern:
        files_to_process = list(DATA_DIR.glob(pattern))
    else:
        # Recursively find all files, excluding hidden files and the checksum file itself
        files_to_process = []
        for root, _, files in os.walk(DATA_DIR):
            for file in files:
                if file.startswith("."):
                    continue
                if file == ".checksums.json":
                    continue
                files_to_process.append(Path(root) / file)

    for file_path in files_to_process:
        try:
            # Store path relative to DATA_DIR for portability
            rel_path = str(file_path.relative_to(DATA_DIR))
            checksums[rel_path] = calculate_sha256(file_path)
        except (FileNotFoundError, IsADirectoryError) as e:
            print(f"Warning: Skipping {file_path} - {e}")
            continue

    return checksums


def save_checksums(checksums: Dict[str, str], output_path: Optional[Path] = None) -> Path:
    """
    Save checksums to a JSON file.

    Args:
        checksums: Dictionary of relative paths to hashes.
        output_path: Optional path to save the JSON. Defaults to DATA_DIR/.checksums.json.

    Returns:
        Path to the saved checksum file.
    """
    if output_path is None:
        output_path = CHECKSUM_FILE

    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "version": "1.0",
        "generated_at": str(Path.cwd()), # Context for reproducibility
        "checksums": checksums
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return output_path


def load_checksums(input_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load checksums from a JSON file.

    Args:
        input_path: Optional path to load from. Defaults to DATA_DIR/.checksums.json.

    Returns:
        Dictionary of relative paths to hashes.

    Raises:
        FileNotFoundError: If the checksum file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if input_path is None:
        input_path = CHECKSUM_FILE

    if not input_path.exists():
        raise FileNotFoundError(f"Checksum file not found: {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("checksums", {})


def verify_integrity(pattern: Optional[str] = None) -> Tuple[bool, List[str]]:
    """
    Verify the integrity of data files against stored checksums.

    Args:
        pattern: Optional glob pattern to verify specific files.

    Returns:
        Tuple of (is_valid, list_of_failed_files).
        is_valid is True if all files match their stored checksums.
    """
    try:
        stored_checksums = load_checksums()
    except FileNotFoundError:
        print("No checksum file found. Run 'generate_checksums' first.")
        return False, ["No checksum file found"]
    except json.JSONDecodeError:
        print("Checksum file is corrupted.")
        return False, ["Checksum file corrupted"]

    # Filter stored checksums if a pattern is provided
    if pattern:
        stored_checksums = {
            k: v for k, v in stored_checksums.items()
            if Path(k).match(pattern) or Path(DATA_DIR / k).match(pattern)
        }

    failed_files = []
    is_valid = True

    for rel_path, expected_hash in stored_checksums.items():
        full_path = DATA_DIR / rel_path

        if not full_path.exists():
            failed_files.append(f"{rel_path}: File missing")
            is_valid = False
            continue

        try:
            current_hash = calculate_sha256(full_path)
            if current_hash != expected_hash:
                failed_files.append(f"{rel_path}: Hash mismatch (expected {expected_hash[:8]}..., got {current_hash[:8]}...)")
                is_valid = False
        except Exception as e:
            failed_files.append(f"{rel_path}: Error reading file - {e}")
            is_valid = False

    return is_valid, failed_files


def main():
    """
    CLI entry point for checksum operations.
    Usage:
      python code/data/checksum_manager.py generate
      python code/data/checksum_manager.py verify
      python code/data/checksum_manager.py verify --pattern "*.json"
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage: python code/data/checksum_manager.py [generate|verify] [--pattern <glob>]")
        sys.exit(1)

    command = sys.argv[1]
    pattern = None

    # Parse optional pattern
    if "--pattern" in sys.argv:
        idx = sys.argv.index("--pattern")
        if idx + 1 < len(sys.argv):
            pattern = sys.argv[idx + 1]

    if command == "generate":
        print(f"Generating checksums for {DATA_DIR}...")
        try:
            checksums = generate_checksums(pattern)
            save_path = save_checksums(checksums)
            print(f"Success. Generated {len(checksums)} checksums. Saved to {save_path}")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif command == "verify":
        print(f"Verifying integrity for {DATA_DIR}...")
        try:
            is_valid, failures = verify_integrity(pattern)
            if is_valid:
                print("All files verified successfully.")
            else:
                print("Integrity check failed. Issues found:")
                for f in failures:
                    print(f"  - {f}")
                sys.exit(1)
        except Exception as e:
            print(f"Error during verification: {e}")
            sys.exit(1)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
