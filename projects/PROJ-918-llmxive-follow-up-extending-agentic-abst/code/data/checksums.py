"""
Checksum management for data integrity verification.
Provides functions to calculate, generate, save, load, and verify file checksums.
"""
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging
logging_config_path = Path(__file__).parent.parent / "logging_config.py"
if logging_config_path.exists():
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from logging_config import setup_logging
    logger = setup_logging(__name__)
else:
    import logging
    logger = logging.getLogger(__name__)
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)


def calculate_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Calculate the hash of a file using the specified algorithm.

    Args:
        file_path: Path to the file to hash
        algorithm: Hash algorithm to use (default: sha256)

    Returns:
        Hexadecimal string representation of the file hash

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the algorithm is not supported
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_func = hashlib.new(algorithm)
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except IOError as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise


def generate_checksums(
    directory: Path,
    recursive: bool = True,
    algorithm: str = "sha256",
    exclude_patterns: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Generate checksums for all files in a directory.

    Args:
        directory: Path to the directory to scan
        recursive: Whether to scan subdirectories recursively
        algorithm: Hash algorithm to use
        exclude_patterns: List of glob patterns to exclude

    Returns:
        Dictionary mapping relative file paths to their checksums
    """
    checksums = {}
    exclude_patterns = exclude_patterns or []

    if recursive:
        file_iter = directory.rglob("*")
    else:
        file_iter = directory.glob("*")

    for file_path in file_iter:
        if file_path.is_dir():
            continue

        # Check exclusion patterns
        rel_path = str(file_path.relative_to(directory))
        if any(
            any(
                file_path.match(p) or rel_path.match(p)
                for p in exclude_patterns
            )
            for exclude_patterns in [exclude_patterns]
        ):
            # Simple pattern matching
            skip = False
            for pattern in exclude_patterns:
                if pattern in rel_path:
                    skip = True
                    break
            if skip:
                continue

        try:
            checksum = calculate_file_hash(file_path, algorithm)
            checksums[rel_path] = checksum
            logger.debug(f"Generated checksum for {rel_path}")
        except Exception as e:
            logger.warning(f"Failed to generate checksum for {file_path}: {e}")

    return checksums


def save_checksums(checksums: Dict[str, str], output_path: Path) -> None:
    """
    Save checksums to a JSON file.

    Args:
        checksums: Dictionary of checksums to save
        output_path: Path to the output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"Saved checksums to {output_path}")


def load_checksums(input_path: Path) -> Dict[str, str]:
    """
    Load checksums from a JSON file.

    Args:
        input_path: Path to the input JSON file

    Returns:
        Dictionary of loaded checksums

    Raises:
        FileNotFoundError: If the file does not exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Checksum file not found: {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        return json.load(f)


def verify_checksums(
    base_directory: Path,
    checksums: Dict[str, str],
    algorithm: str = "sha256"
) -> Tuple[Dict[str, str], Dict[str, str], List[str]]:
    """
    Verify files against a set of checksums.

    Args:
        base_directory: Base directory for the files
        checksums: Dictionary of expected checksums
        algorithm: Hash algorithm to use

    Returns:
        Tuple of (verified_checksums, mismatched_checksums, missing_files)
    """
    verified = {}
    mismatched = {}
    missing = []

    for rel_path, expected_hash in checksums.items():
        file_path = base_directory / rel_path

        if not file_path.exists():
            missing.append(rel_path)
            continue

        try:
            actual_hash = calculate_file_hash(file_path, algorithm)
            if actual_hash == expected_hash:
                verified[rel_path] = actual_hash
            else:
                mismatched[rel_path] = {
                    "expected": expected_hash,
                    "actual": actual_hash
                }
        except Exception as e:
            logger.error(f"Error verifying {file_path}: {e}")
            mismatched[rel_path] = {"error": str(e)}

    return verified, mismatched, missing


def main() -> int:
    """
    Main entry point for checksum operations.
    Supports 'generate' and 'verify' subcommands.

    Usage:
        python code/data/checksums.py generate <directory> [output_file]
        python code/data/checksums.py verify <base_directory> <checksum_file>

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python code/data/checksums.py generate <directory> [output_file]")
        print("  python code/data/checksums.py verify <base_directory> <checksum_file>")
        return 1

    command = sys.argv[1]
    base_directory = Path(sys.argv[2])

    if not base_directory.exists():
        logger.error(f"Directory not found: {base_directory}")
        return 1

    if command == "generate":
        output_file = Path(sys.argv[3]) if len(sys.argv) > 3 else base_directory / "checksums.json"
        logger.info(f"Generating checksums for {base_directory}")
        checksums = generate_checksums(base_directory)

        if not checksums:
            logger.warning("No files found to checksum")
            return 1

        save_checksums(checksums, output_file)
        print(f"Generated {len(checksums)} checksums")
        print(f"Saved to: {output_file}")
        return 0

    elif command == "verify":
        if len(sys.argv) < 4:
            print("Usage: python code/data/checksums.py verify <base_directory> <checksum_file>")
            return 1

        checksum_file = Path(sys.argv[3])
        if not checksum_file.exists():
            logger.error(f"Checksum file not found: {checksum_file}")
            return 1

        try:
            expected_checksums = load_checksums(checksum_file)
        except Exception as e:
            logger.error(f"Failed to load checksums: {e}")
            return 1

        logger.info(f"Verifying {len(expected_checksums)} files in {base_directory}")
        verified, mismatched, missing = verify_checksums(base_directory, expected_checksums)

        print(f"Verified: {len(verified)} files")
        if mismatched:
            print(f"Mismatched: {len(mismatched)} files")
            for path, details in mismatched.items():
                print(f"  - {path}: {details}")
        if missing:
            print(f"Missing: {len(missing)} files")
            for path in missing:
                print(f"  - {path}")

        if mismatched or missing:
            return 1
        return 0

    else:
        logger.error(f"Unknown command: {command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
