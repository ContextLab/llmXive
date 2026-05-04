"""
Checksum utilities for data artifact integrity verification.

This module provides SHA256 checksum computation, validation, and
caching utilities for ensuring data provenance and integrity across
the project pipeline.

Per Constitution Principle III, all data artifacts must have recorded
checksums for reproducibility verification.
"""
import os
import sys
import hashlib
import logging
import json
from pathlib import Path
from typing import Dict, Optional, List, Tuple, Any
from dataclasses import dataclass, asdict, field

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class ChecksumRecord:
    """Record of a file's checksum and metadata."""
    path: str
    checksum: str
    size_bytes: int
    modified_time: float
    algorithm: str = "sha256"

@dataclass
class ChecksumCache:
    """Container for all checksum records."""
    records: Dict[str, ChecksumRecord] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    version: str = "1.0"

def compute_file_checksum_sha256(
    file_path: Path,
    chunk_size: int = 8192
) -> str:
    """
    Compute SHA256 checksum of a file.

    Args:
        file_path: Path to the file to hash
        chunk_size: Size of chunks to read (default 8KB)

    Returns:
        Hexadecimal SHA256 hash string

    Raises:
        FileNotFoundError: If file does not exist
        PermissionError: If file cannot be read
    """
    sha256_hash = hashlib.sha256()
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)

    return sha256_hash.hexdigest()

def compute_string_checksum_sha256(data: str) -> str:
    """
    Compute SHA256 checksum of a string.

    Args:
        data: String to hash

    Returns:
        Hexadecimal SHA256 hash string
    """
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

def validate_checksum(
    file_path: Path,
    expected_checksum: str,
    algorithm: str = "sha256"
) -> Tuple[bool, str]:
    """
    Validate a file's checksum against an expected value.

    Args:
        file_path: Path to the file to validate
        expected_checksum: Expected checksum value
        algorithm: Hash algorithm to use (default: sha256)

    Returns:
        Tuple of (is_valid, message)
    """
    file_path = Path(file_path)

    if not file_path.exists():
        return False, f"File not found: {file_path}"

    try:
        actual_checksum = compute_file_checksum_sha256(file_path)

        if actual_checksum.lower() == expected_checksum.lower():
            return True, f"Checksum validated: {actual_checksum}"
        else:
            return False, (
                f"Checksum mismatch. Expected: {expected_checksum}, "
                f"Got: {actual_checksum}"
            )
    except Exception as e:
        return False, f"Checksum validation failed: {str(e)}"

def load_checksum_cache(cache_path: Path) -> ChecksumCache:
    """
    Load checksum cache from a JSON file.

    Args:
        cache_path: Path to the checksum cache file

    Returns:
        ChecksumCache object

    Raises:
        FileNotFoundError: If cache file does not exist
        json.JSONDecodeError: If cache file is invalid JSON
    """
    cache_path = Path(cache_path)

    if not cache_path.exists():
        # Return empty cache if file doesn't exist
        logger.info(f"Checksum cache not found, creating new: {cache_path}")
        return ChecksumCache()

    with open(cache_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    records = {}
    for path_str, record_data in data.get("records", {}).items():
        records[path_str] = ChecksumRecord(**record_data)

    return ChecksumCache(
        records=records,
        created_at=data.get("created_at", ""),
        updated_at=data.get("updated_at", ""),
        version=data.get("version", "1.0")
    )

def save_checksum_cache(
    cache: ChecksumCache,
    cache_path: Path
) -> None:
    """
    Save checksum cache to a JSON file.

    Args:
        cache: ChecksumCache object to save
        cache_path: Path to save the cache file
    """
    cache_path = Path(cache_path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    import datetime
    now = datetime.datetime.now().isoformat()

    if not cache.created_at:
        cache.created_at = now
    cache.updated_at = now

    # Convert ChecksumRecord objects to dicts
    records_dict = {
        path: asdict(record)
        for path, record in cache.records.items()
    }

    cache_data = {
        "records": records_dict,
        "created_at": cache.created_at,
        "updated_at": cache.updated_at,
        "version": cache.version
    }

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, indent=2)

    logger.info(f"Checksum cache saved to: {cache_path}")

def generate_checksums_for_directory(
    directory: Path,
    extensions: Optional[List[str]] = None,
    recursive: bool = True
) -> ChecksumCache:
    """
    Generate checksums for all files in a directory.

    Args:
        directory: Directory to scan for files
        extensions: List of file extensions to include (e.g., ['.csv', '.json'])
                   If None, include all files
        recursive: If True, scan subdirectories recursively

    Returns:
        ChecksumCache with all file checksums
    """
    directory = Path(directory)
    cache = ChecksumCache()

    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return cache

    for root, dirs, files in os.walk(directory):
        if not recursive and root != str(directory):
            continue

        for filename in files:
            # Skip hidden files and common non-data files
            if filename.startswith(".") or filename.endswith(
                (".pyc", ".pyo", ".log", ".tmp")
            ):
                continue

            # Filter by extension if specified
            if extensions:
                if not any(filename.endswith(ext) for ext in extensions):
                    continue

            file_path = Path(root) / filename
            relative_path = str(file_path.relative_to(directory))

            try:
                checksum = compute_file_checksum_sha256(file_path)
                stat = file_path.stat()

                cache.records[relative_path] = ChecksumRecord(
                    path=relative_path,
                    checksum=checksum,
                    size_bytes=stat.st_size,
                    modified_time=stat.st_mtime
                )
            except Exception as e:
                logger.error(f"Failed to checksum {file_path}: {e}")

    return cache

def verify_checksums(
    directory: Path,
    cache: ChecksumCache
) -> Dict[str, bool]:
    """
    Verify all files in a directory against cached checksums.

    Args:
        directory: Directory containing files to verify
        cache: ChecksumCache with expected checksums

    Returns:
        Dict mapping file paths to validation results (True/False)
    """
    results = {}

    for relative_path, record in cache.records.items():
        file_path = directory / relative_path

        if not file_path.exists():
            results[relative_path] = False
            logger.warning(f"File not found during verification: {file_path}")
            continue

        is_valid, message = validate_checksum(file_path, record.checksum)
        results[relative_path] = is_valid

        if not is_valid:
            logger.warning(f"Checksum failed for {relative_path}: {message}")

    return results

def update_checksum(
    cache: ChecksumCache,
    file_path: Path,
    relative_base: Path
) -> ChecksumRecord:
    """
    Update checksum for a single file in the cache.

    Args:
        cache: ChecksumCache to update
        file_path: Path to the file to checksum
        relative_base: Base path for computing relative path

    Returns:
        The updated ChecksumRecord
    """
    file_path = Path(file_path)
    relative_base = Path(relative_base)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    relative_path = str(file_path.relative_to(relative_base))
    checksum = compute_file_checksum_sha256(file_path)
    stat = file_path.stat()

    record = ChecksumRecord(
        path=relative_path,
        checksum=checksum,
        size_bytes=stat.st_size,
        modified_time=stat.st_mtime
    )

    cache.records[relative_path] = record
    return record

def get_checksum_for_file(
    file_path: Path,
    cache: ChecksumCache
) -> Optional[str]:
    """
    Get cached checksum for a file.

    Args:
        file_path: Path to the file
        cache: ChecksumCache to search

    Returns:
        Checksum string if found, None otherwise
    """
    file_path = Path(file_path)

    for relative_path, record in cache.records.items():
        if record.path == str(file_path):
            return record.checksum

    return None

def main():
    """
    Command-line interface for checksum utilities.

    Usage:
        python -m src.utils.checksums --help
        python -m src.utils.checksums compute <file_path>
        python -m src.utils.checksums validate <file_path> <expected_checksum>
        python -m src.utils.checksums generate <directory> --output <cache_file>
        python -m src.utils.checksums verify <directory> --cache <cache_file>
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Checksum utilities for data integrity verification"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Compute command
    compute_parser = subparsers.add_parser(
        "compute", help="Compute SHA256 checksum of a file"
    )
    compute_parser.add_argument("file_path", help="Path to file")

    # Validate command
    validate_parser = subparsers.add_parser(
        "validate", help="Validate file against expected checksum"
    )
    validate_parser.add_argument("file_path", help="Path to file")
    validate_parser.add_argument("expected_checksum", help="Expected checksum")

    # Generate command
    generate_parser = subparsers.add_parser(
        "generate", help="Generate checksums for all files in directory"
    )
    generate_parser.add_argument("directory", help="Directory to scan")
    generate_parser.add_argument(
        "--output", "-o", help="Output cache file path"
    )
    generate_parser.add_argument(
        "--recursive", "-r", action="store_true",
        help="Scan subdirectories recursively (default: True)"
    )

    # Verify command
    verify_parser = subparsers.add_parser(
        "verify", help="Verify files against cached checksums"
    )
    verify_parser.add_argument("directory", help="Directory containing files")
    verify_parser.add_argument(
        "--cache", "-c", required=True, help="Checksum cache file path"
    )

    args = parser.parse_args()

    if args.command == "compute":
        checksum = compute_file_checksum_sha256(Path(args.file_path))
        print(f"{checksum}  {args.file_path}")

    elif args.command == "validate":
        is_valid, message = validate_checksum(
            Path(args.file_path), args.expected_checksum
        )
        print(f"Valid: {is_valid}")
        print(f"Message: {message}")

    elif args.command == "generate":
        cache = generate_checksums_for_directory(
            Path(args.directory),
            recursive=args.recursive
        )
        if args.output:
            save_checksum_cache(cache, Path(args.output))
            print(f"Checksums saved to: {args.output}")
        else:
            print(f"Generated {len(cache.records)} checksums:")
            for path, record in cache.records.items():
                print(f"  {record.checksum}  {path}")

    elif args.command == "verify":
        cache = load_checksum_cache(Path(args.cache))
        results = verify_checksums(Path(args.directory), cache)

        passed = sum(1 for v in results.values() if v)
        failed = sum(1 for v in results.values() if not v)

        print(f"Verification complete: {passed} passed, {failed} failed")
        for path, valid in results.items():
            status = "✓" if valid else "✗"
            print(f"  {status} {path}")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
