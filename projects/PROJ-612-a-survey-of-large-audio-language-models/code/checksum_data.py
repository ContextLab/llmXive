"""
Data Hygiene and Checksum Infrastructure for llmXive.

This module provides utilities to verify SHA-256 hashes of downloaded datasets
to ensure data integrity and reproducibility.
"""

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Project root relative to this file (code/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CHECKSUM_MANIFEST_PATH = DATA_DIR / "checksums_manifest.json"


def calculate_sha256(file_path: Path) -> str:
    """
    Calculate the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")


def load_manifest() -> Dict[str, str]:
    """
    Load the checksum manifest from disk.

    Returns:
        Dictionary mapping relative file paths to their expected SHA-256 hashes.
    """
    if not CHECKSUM_MANIFEST_PATH.exists():
        return {}
    try:
        with open(CHECKSUM_MANIFEST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load manifest {CHECKSUM_MANIFEST_PATH}: {e}", file=sys.stderr)
        return {}


def save_manifest(manifest: Dict[str, str]) -> None:
    """
    Save the checksum manifest to disk.

    Args:
        manifest: Dictionary mapping relative file paths to SHA-256 hashes.
    """
    CHECKSUM_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CHECKSUM_MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)


def register_file(file_path: Path, relative_path: Optional[str] = None) -> str:
    """
    Calculate hash for a file and add it to the manifest.

    Args:
        file_path: Absolute path to the file.
        relative_path: Optional relative path to store (defaults to path relative to data/).

    Returns:
        The calculated SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot register non-existent file: {file_path}")

    # Determine the key for the manifest
    if relative_path is None:
        if str(file_path).startswith(str(DATA_DIR)):
            relative_path = str(file_path.relative_to(DATA_DIR))
        else:
            relative_path = str(file_path)

    manifest = load_manifest()
    current_hash = calculate_sha256(file_path)
    manifest[relative_path] = current_hash
    save_manifest(manifest)
    print(f"Registered: {relative_path} (SHA-256: {current_hash[:16]}...)")
    return current_hash


def verify_file(file_path: Path, expected_hash: str, relative_path: Optional[str] = None) -> bool:
    """
    Verify a single file against an expected hash.

    Args:
        file_path: Absolute path to the file to check.
        expected_hash: The expected SHA-256 hex string.
        relative_path: Optional path for logging purposes.

    Returns:
        True if hash matches, False otherwise.
    """
    if not file_path.exists():
        print(f"MISSING: {file_path}", file=sys.stderr)
        return False

    actual_hash = calculate_sha256(file_path)
    display_path = relative_path or str(file_path)

    if actual_hash == expected_hash:
        print(f"OK: {display_path}")
        return True
    else:
        print(f"MISMATCH: {display_path}", file=sys.stderr)
        print(f"  Expected: {expected_hash}", file=sys.stderr)
        print(f"  Actual:   {actual_hash}", file=sys.stderr)
        return False


def verify_all() -> Tuple[int, int]:
    """
    Verify all files listed in the checksum manifest.

    Returns:
        Tuple of (passed_count, failed_count).
    """
    manifest = load_manifest()
    if not manifest:
        print("No checksums found in manifest.", file=sys.stderr)
        return 0, 0

    passed = 0
    failed = 0

    for rel_path, expected_hash in manifest.items():
        file_path = DATA_DIR / rel_path
        if verify_file(file_path, expected_hash, rel_path):
            passed += 1
        else:
            failed += 1

    print(f"\nVerification Complete: {passed} passed, {failed} failed.")
    return passed, failed


def generate_checksums_for_directory(directory: Path) -> Dict[str, str]:
    """
    Recursively generate checksums for all files in a directory.

    Args:
        directory: Path to the directory to scan.

    Returns:
        Dictionary of relative paths to hashes.
    """
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    checksums = {}
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            try:
                rel_path = str(file_path.relative_to(DATA_DIR))
                checksums[rel_path] = calculate_sha256(file_path)
            except ValueError:
                # File is not under DATA_DIR, skip or handle differently
                continue
    return checksums


def main():
    """CLI entry point for checksum operations."""
    import argparse

    parser = argparse.ArgumentParser(description="Data Checksum Utility")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # verify command
    verify_parser = subparsers.add_parser("verify", help="Verify files against manifest")
    verify_parser.add_argument("--file", type=str, help="Verify specific file (relative to data/)")

    # register command
    reg_parser = subparsers.add_parser("register", help="Register files to manifest")
    reg_parser.add_argument("files", nargs="+", help="Files to register (absolute or relative to data/)")

    # generate command
    gen_parser = subparsers.add_parser("generate", help="Generate manifest for all files in data/")

    args = parser.parse_args()

    if args.command == "verify":
        if args.file:
            file_path = DATA_DIR / args.file
            manifest = load_manifest()
            if args.file not in manifest:
                print(f"Error: {args.file} not found in manifest.", file=sys.stderr)
                sys.exit(1)
            success = verify_file(file_path, manifest[args.file], args.file)
            sys.exit(0 if success else 1)
        else:
            passed, failed = verify_all()
            sys.exit(0 if failed == 0 else 1)

    elif args.command == "register":
        for file_arg in args.files:
            file_path = Path(file_arg)
            if not file_path.is_absolute():
                # Assume relative to data/ if not absolute
                file_path = DATA_DIR / file_arg
            try:
                register_file(file_path)
            except FileNotFoundError as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)

    elif args.command == "generate":
        print(f"Scanning {DATA_DIR}...")
        new_checksums = generate_checksums_for_directory(DATA_DIR)
        save_manifest(new_checksums)
        print(f"Generated manifest with {len(new_checksums)} files.")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
