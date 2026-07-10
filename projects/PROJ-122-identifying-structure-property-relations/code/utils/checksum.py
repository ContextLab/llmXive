"""
Checksum utility for raw data integrity verification.

This module provides functions to compute and validate SHA-256 checksums
for data files, ensuring data integrity throughout the research pipeline.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from .schema_validator import validate_sha256_checksum


def compute_file_checksum(file_path: Union[str, Path], chunk_size: int = 8192) -> str:
    """
    Compute the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file to checksum.
        chunk_size: Size of chunks to read at a time (default 8KB).

    Returns:
        Hexadecimal SHA-256 checksum string.

    Raises:
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If the path points to a directory.
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if file_path.is_dir():
        raise IsADirectoryError(f"Path is a directory, not a file: {file_path}")

    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()


def compute_directory_checksums(directory_path: Union[str, Path]) -> Dict[str, str]:
    """
    Compute SHA-256 checksums for all files in a directory (non-recursive).

    Args:
        directory_path: Path to the directory.

    Returns:
        Dictionary mapping filenames to their SHA-256 checksums.
    """
    directory_path = Path(directory_path)
    
    if not directory_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    
    if not directory_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {directory_path}")

    checksums = {}
    
    for file_path in directory_path.iterdir():
        if file_path.is_file():
            checksums[file_path.name] = compute_file_checksum(file_path)
    
    return checksums


def validate_file_checksum(
    file_path: Union[str, Path], 
    expected_checksum: str
) -> Tuple[bool, str]:
    """
    Validate a file's checksum against an expected value.

    Args:
        file_path: Path to the file.
        expected_checksum: Expected SHA-256 checksum (hex string).

    Returns:
        Tuple of (is_valid, message) where is_valid is True if checksums match.
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return False, f"File not found: {file_path}"

    try:
        actual_checksum = compute_file_checksum(file_path)
    except Exception as e:
        return False, f"Error computing checksum: {str(e)}"

    # Normalize checksums to lowercase for comparison
    if actual_checksum.lower() == expected_checksum.lower():
        return True, f"Checksum valid for {file_path.name}"
    else:
        return False, f"Checksum mismatch for {file_path.name}: " \
                     f"expected {expected_checksum}, got {actual_checksum}"


def save_checksums(
    checksums: Dict[str, str], 
    output_path: Union[str, Path]
) -> Path:
    """
    Save checksums to a JSON file.

    Args:
        checksums: Dictionary mapping filenames to checksums.
        output_path: Path to the output JSON file.

    Returns:
        Path to the created file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    checksum_data = {
        "checksums": checksums,
        "algorithm": "sha256"
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(checksum_data, f, indent=2)

    return output_path


def load_checksums(checksum_path: Union[str, Path]) -> Dict[str, str]:
    """
    Load checksums from a JSON file.

    Args:
        checksum_path: Path to the JSON file containing checksums.

    Returns:
        Dictionary mapping filenames to checksums.
    """
    checksum_path = Path(checksum_path)
    
    if not checksum_path.exists():
        raise FileNotFoundError(f"Checksum file not found: {checksum_path}")

    with open(checksum_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("checksums", {})


def generate_checksum_manifest(
    input_directory: Union[str, Path],
    output_path: Union[str, Path]
) -> Path:
    """
    Generate a manifest file with checksums for all files in a directory.

    Args:
        input_directory: Directory to scan for files.
        output_path: Path to write the manifest JSON file.

    Returns:
        Path to the created manifest file.
    """
    input_directory = Path(input_directory)
    output_path = Path(output_path)

    if not input_directory.exists():
        raise FileNotFoundError(f"Input directory not found: {input_directory}")

    checksums = compute_directory_checksums(input_directory)
    return save_checksums(checksums, output_path)


def verify_checksum_manifest(
    manifest_path: Union[str, Path],
    base_directory: Optional[Union[str, Path]] = None
) -> Dict[str, Tuple[bool, str]]:
    """
    Verify files against a checksum manifest.

    Args:
        manifest_path: Path to the manifest JSON file.
        base_directory: Base directory for file paths (defaults to manifest's directory).

    Returns:
        Dictionary mapping filenames to (is_valid, message) tuples.
    """
    manifest_path = Path(manifest_path)
    
    if base_directory is None:
        base_directory = manifest_path.parent
    else:
        base_directory = Path(base_directory)

    expected_checksums = load_checksums(manifest_path)
    results = {}

    for filename, expected_checksum in expected_checksums.items():
        file_path = base_directory / filename
        is_valid, message = validate_file_checksum(file_path, expected_checksum)
        results[filename] = (is_valid, message)

    return results


def main():
    """
    Command-line interface for checksum utility.
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage: python checksum.py <command> [args...]")
        print("Commands:")
        print("  compute <file>              - Compute checksum of a file")
        print("  validate <file> <checksum>  - Validate file against checksum")
        print("  manifest <dir> <output>     - Generate manifest for directory")
        print("  verify <manifest> [dir]     - Verify files against manifest")
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == "compute":
            if len(sys.argv) < 3:
                print("Error: File path required")
                sys.exit(1)
            file_path = sys.argv[2]
            checksum = compute_file_checksum(file_path)
            print(f"{checksum}  {file_path}")

        elif command == "validate":
            if len(sys.argv) < 4:
                print("Error: File path and checksum required")
                sys.exit(1)
            file_path = sys.argv[2]
            expected_checksum = sys.argv[3]
            is_valid, message = validate_file_checksum(file_path, expected_checksum)
            print(message)
            sys.exit(0 if is_valid else 1)

        elif command == "manifest":
            if len(sys.argv) < 4:
                print("Error: Directory and output path required")
                sys.exit(1)
            input_dir = sys.argv[2]
            output_path = sys.argv[3]
            manifest_path = generate_checksum_manifest(input_dir, output_path)
            print(f"Manifest created: {manifest_path}")

        elif command == "verify":
            if len(sys.argv) < 3:
                print("Error: Manifest path required")
                sys.exit(1)
            manifest_path = sys.argv[2]
            base_dir = sys.argv[3] if len(sys.argv) > 3 else None
            results = verify_checksum_manifest(manifest_path, base_dir)
            
            all_valid = True
            for filename, (is_valid, message) in results.items():
                status = "✓" if is_valid else "✗"
                print(f"{status} {filename}: {message}")
                if not is_valid:
                    all_valid = False
            
            sys.exit(0 if all_valid else 1)

        else:
            print(f"Unknown command: {command}")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
