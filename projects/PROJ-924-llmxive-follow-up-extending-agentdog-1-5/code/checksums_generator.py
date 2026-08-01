import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, List

from config import get_path, ensure_directories
from utils import load_json_file, save_json_file


def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file to hash.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal string of the file's checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_obj = hashlib.new(algorithm)
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(8192), b""):
                hash_obj.update(chunk)
    except IOError as e:
        raise ValueError(f"Could not read file {file_path}: {e}")

    return hash_obj.hexdigest()


def generate_checksums(file_paths: List[Path], algorithm: str = "sha256") -> Dict[str, str]:
    """
    Generate checksums for a list of files.

    Args:
        file_paths: List of file paths to compute checksums for.
        algorithm: Hash algorithm to use.

    Returns:
        Dictionary mapping relative file paths to their checksums.

    Raises:
        FileNotFoundError: If any file is missing.
    """
    checksums = {}
    for file_path in file_paths:
        if not file_path.is_absolute():
            # Resolve relative to project root if not absolute
            project_root = get_path("project_root")
            file_path = project_root / file_path

        checksum = compute_file_checksum(file_path, algorithm)
        # Store relative path for portability
        relative_path = str(file_path.relative_to(get_path("project_root")))
        checksums[relative_path] = checksum

    return checksums


def save_checksums(checksums: Dict[str, str], output_path: Path) -> None:
    """
    Save checksums to a JSON file.

    Args:
        checksums: Dictionary of file paths to checksums.
        output_path: Path to the output JSON file.
    """
    ensure_directories([output_path.parent])
    data = {
        "algorithm": "sha256",
        "files": checksums
    }
    save_json_file(data, output_path)


def main() -> None:
    """
    Main entry point to generate checksums for raw data files.

    This script scans the data/raw directory for supported files,
    computes their checksums, and saves them to data/checksums.json.
    """
    project_root = get_path("project_root")
    raw_dir = get_path("raw_data")
    output_file = get_path("checksums")

    if not raw_dir.exists():
        print(f"Warning: Raw data directory does not exist: {raw_dir}")
        # Initialize with empty checksums if directory is missing
        save_checksums({}, output_file)
        return

    # Define supported extensions for raw data
    supported_extensions = {".json", ".jsonl", ".csv", ".txt", ".parquet"}

    file_paths: List[Path] = []
    for ext in supported_extensions:
        file_paths.extend(raw_dir.glob(f"*{ext}"))

    if not file_paths:
        print(f"No raw data files found in {raw_dir}")
        # Save empty checksums if no files found
        save_checksums({}, output_file)
        return

    print(f"Found {len(file_paths)} raw data files to checksum.")
    checksums = generate_checksums(file_paths)
    save_checksums(checksums, output_file)
    print(f"Checksums saved to {output_file}")


if __name__ == "__main__":
    main()
