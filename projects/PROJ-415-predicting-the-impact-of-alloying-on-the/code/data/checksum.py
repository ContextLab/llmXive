"""
Checksum utilities for data integrity verification.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from config import DATA_DIR

CHECKSUM_FILE = DATA_DIR / "checksums.json"


def compute_sha256(file_path: Path) -> str:
    """
    Compute SHA256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def generate_checksums(directory: Path, extensions: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Generate checksums for all files in a directory (recursive).

    Args:
        directory: Root directory to scan.
        extensions: Optional list of file extensions to include (e.g., ['.csv', '.json']).
                    If None, includes all files.

    Returns:
        Dictionary mapping relative file paths to their SHA256 hashes.
    """
    checksums = {}
    if not directory.exists():
        return checksums

    for file_path in directory.rglob("*"):
        if file_path.is_file():
            if extensions is None or any(file_path.suffix == ext for ext in extensions):
                rel_path = file_path.relative_to(directory)
                checksums[str(rel_path)] = compute_sha256(file_path)

    return checksums


def save_checksums(checksums: Dict[str, str], output_path: Optional[Path] = None) -> None:
    """
    Save checksums to a JSON file.

    Args:
        checksums: Dictionary of file paths to hashes.
        output_path: Path to save the JSON file. Defaults to DATA_DIR/checksums.json.
    """
    if output_path is None:
        output_path = CHECKSUM_FILE

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(checksums, f, indent=2)


def load_checksums(input_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load checksums from a JSON file.

    Args:
        input_path: Path to the JSON file. Defaults to DATA_DIR/checksums.json.

    Returns:
        Dictionary of file paths to hashes, or empty dict if file doesn't exist.
    """
    if input_path is None:
        input_path = CHECKSUM_FILE

    if not input_path.exists():
        return {}

    with open(input_path, "r") as f:
        return json.load(f)


def verify_checksums(directory: Path, input_path: Optional[Path] = None) -> bool:
    """
    Verify current files against stored checksums.

    Args:
        directory: Root directory to verify.
        input_path: Path to the checksums JSON file.

    Returns:
        True if all files match, False otherwise. Prints mismatches to stdout.
    """
    stored = load_checksums(input_path)
    if not stored:
        print("No stored checksums found. Run 'generate' first.")
        return False

    current = generate_checksums(directory)
    all_valid = True

    for file_str, stored_hash in stored.items():
        file_path = directory / file_str
        if not file_path.exists():
            print(f"MISSING: {file_str}")
            all_valid = False
            continue

        current_hash = current.get(file_str)
        if current_hash != stored_hash:
            print(f"MISMATCH: {file_str}")
            print(f"  Expected: {stored_hash}")
            print(f"  Found:    {current_hash}")
            all_valid = False
        else:
            print(f"OK: {file_str}")

    # Check for new files not in checksums
    for file_str in current:
        if file_str not in stored:
            print(f"NEW FILE (not in checksums): {file_str}")

    return all_valid


def main():
    """CLI entry point for checksum operations."""
    import argparse

    parser = argparse.ArgumentParser(description="Data checksum utilities")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate checksums for data directory")
    gen_parser.add_argument("--extensions", nargs="+", help="File extensions to include (e.g. .csv .json)")
    gen_parser.add_argument("--output", type=Path, help="Output path for checksums.json")

    # Verify command
    ver_parser = subparsers.add_parser("verify", help="Verify data against stored checksums")
    ver_parser.add_argument("--input", type=Path, help="Path to checksums.json")

    args = parser.parse_args()

    if args.command == "generate":
        checksums = generate_checksums(DATA_DIR, args.extensions)
        output_path = args.output if args.output else CHECKSUM_FILE
        save_checksums(checksums, output_path)
        print(f"Generated {len(checksums)} checksums saved to {output_path}")
    elif args.command == "verify":
        success = verify_checksums(DATA_DIR, args.input)
        if success:
            print("All checksums verified successfully.")
        else:
            print("Verification failed. Check output above.")
            exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
