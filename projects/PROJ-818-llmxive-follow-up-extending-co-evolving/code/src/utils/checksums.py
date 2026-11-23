"""
Checksum utility for managing SHA-256 hashes of data artifacts.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


class ChecksumError(Exception):
    """Custom exception for checksum-related errors."""
    pass


def compute_file_sha256(file_path: str) -> str:
    """
    Compute the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        ChecksumError: If the file does not exist or cannot be read.
    """
    path = Path(file_path)
    if not path.exists():
        raise ChecksumError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise ChecksumError(f"Error reading file {file_path}: {e}")


def load_checksums(checksum_file_path: str = "data/checksums.json") -> Dict[str, Any]:
    """
    Load the checksums database from disk.

    Args:
        checksum_file_path: Path to the checksums JSON file.

    Returns:
        Dictionary containing the checksums data.
        Returns an empty dict if the file does not exist.
    """
    path = Path(checksum_file_path)
    if not path.exists():
        return {"files": {}, "metadata": {"last_updated": None}}

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ChecksumError(f"Invalid JSON in checksum file {checksum_file_path}: {e}")


def save_checksums(checksums: Dict[str, Any], checksum_file_path: str = "data/checksums.json") -> None:
    """
    Save the checksums database to disk.

    Args:
        checksums: Dictionary containing the checksums data.
        checksum_file_path: Path to the checksums JSON file.
    """
    path = Path(checksum_file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    checksums["metadata"]["last_updated"] = datetime.utcnow().isoformat()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2)


def update_checksum_for_file(file_path: str, checksum_file_path: str = "data/checksums.json") -> str:
    """
    Compute the hash of a file and update the checksums database.

    Args:
        file_path: Path to the file to hash and register.
        checksum_file_path: Path to the checksums JSON file.

    Returns:
        The computed SHA-256 hash.
    """
    hash_value = compute_file_sha256(file_path)
    checksums = load_checksums(checksum_file_path)

    # Use relative path from project root for consistency if possible,
    # otherwise store absolute or provided path.
    file_key = str(Path(file_path).relative_to(Path.cwd())) if Path(file_path).is_relative_to(Path.cwd()) else file_path

    checksums["files"][file_key] = {
        "hash": hash_value,
        "updated_at": datetime.utcnow().isoformat()
    }

    save_checksums(checksums, checksum_file_path)
    return hash_value


def verify_file_integrity(file_path: str, checksum_file_path: str = "data/checksums.json") -> bool:
    """
    Verify a file's integrity against the stored checksum.

    Args:
        file_path: Path to the file to verify.
        checksum_file_path: Path to the checksums JSON file.

    Returns:
        True if the file matches the stored checksum, False otherwise.

    Raises:
        ChecksumError: If the file is not registered in the checksums database.
    """
    path = Path(file_path)
    if not path.exists():
        raise ChecksumError(f"File not found for verification: {file_path}")

    checksums = load_checksums(checksum_file_path)

    file_key = str(Path(file_path).relative_to(Path.cwd())) if Path(file_path).is_relative_to(Path.cwd()) else file_path

    if file_key not in checksums.get("files", {}):
        raise ChecksumError(f"File not registered in checksums database: {file_key}")

    stored_hash = checksums["files"][file_key]["hash"]
    current_hash = compute_file_sha256(file_path)

    return stored_hash == current_hash


def main() -> None:
    """
    CLI entry point for checksum utility.
    Usage:
      python -m src.utils.checksums compute <file_path>
      python -m src.utils.checksums update <file_path>
      python -m src.utils.checksums verify <file_path>
      python -m src.utils.checksums list
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.utils.checksums <command> [args]")
        print("Commands: compute, update, verify, list")
        sys.exit(1)

    command = sys.argv[1]

    if command == "compute":
        if len(sys.argv) < 3:
            print("Error: Missing file path")
            sys.exit(1)
        file_path = sys.argv[2]
        try:
            h = compute_file_sha256(file_path)
            print(f"SHA-256: {h}")
        except ChecksumError as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif command == "update":
        if len(sys.argv) < 3:
            print("Error: Missing file path")
            sys.exit(1)
        file_path = sys.argv[2]
        try:
            h = update_checksum_for_file(file_path)
            print(f"Updated checksum for {file_path}: {h}")
        except ChecksumError as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif command == "verify":
        if len(sys.argv) < 3:
            print("Error: Missing file path")
            sys.exit(1)
        file_path = sys.argv[2]
        try:
            valid = verify_file_integrity(file_path)
            if valid:
                print(f"Integrity check passed for {file_path}")
            else:
                print(f"Integrity check FAILED for {file_path}")
                sys.exit(1)
        except ChecksumError as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif command == "list":
        checksums = load_checksums()
        if not checksums.get("files"):
            print("No checksums registered.")
        else:
            print("Registered files:")
            for fname, info in checksums["files"].items():
                print(f"  {fname}: {info['hash'][:16]}... (updated: {info['updated_at']})")
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
