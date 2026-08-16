import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from config import DATA_DIR


def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def generate_checksums(
    directory: Path, recursive: bool = True, extensions: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Generate checksums for all files in a directory.

    Args:
        directory: Root directory to scan
        recursive: Whether to scan subdirectories
        extensions: Optional list of file extensions to include (e.g., ['.csv', '.json'])

    Returns:
        Dictionary mapping relative file paths to their SHA256 checksums
    """
    checksums = {}
    dir_path = Path(directory)

    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")

    if recursive:
        files = list(dir_path.rglob("*"))
    else:
        files = list(dir_path.glob("*"))

    for file_path in files:
        if file_path.is_file():
            if extensions:
                if file_path.suffix.lower() not in extensions:
                    continue

            rel_path = file_path.relative_to(dir_path)
            checksum = compute_sha256(file_path)
            checksums[str(rel_path)] = checksum

    return checksums


def save_checksums(checksums: Dict[str, str], output_path: Path) -> None:
    """Save checksums to a JSON file."""
    with open(output_path, "w") as f:
        json.dump(checksums, f, indent=2)


def load_checksums(input_path: Path) -> Dict[str, str]:
    """Load checksums from a JSON file."""
    with open(input_path, "r") as f:
        return json.load(f)


def verify_checksums(
    directory: Path,
    checksums: Dict[str, str],
    verbose: bool = False,
) -> bool:
    """
    Verify file checksums against stored values.

    Args:
        directory: Root directory where files are located
        checksums: Dictionary of expected checksums
        verbose: Whether to print verification details

    Returns:
        True if all files verify correctly, False otherwise
    """
    all_valid = True

    for rel_path, expected_checksum in checksums.items():
        file_path = directory / rel_path

        if not file_path.exists():
            if verbose:
                print(f"MISSING: {rel_path}")
            all_valid = False
            continue

        actual_checksum = compute_sha256(file_path)

        if actual_checksum != expected_checksum:
            if verbose:
                print(f"MISMATCH: {rel_path}")
                print(f"  Expected: {expected_checksum}")
                print(f"  Actual:   {actual_checksum}")
            all_valid = False
        elif verbose:
            print(f"OK: {rel_path}")

    return all_valid


def main() -> None:
    """Main entry point for checksum operations."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m data.checksum <command> [args]")
        print("Commands:")
        print("  generate [dir]  - Generate checksums for directory (default: data/)")
        print("  verify [dir]    - Verify checksums against data/checksums.json")
        print("  verify-file <file> - Verify a single file against stored checksums")
        sys.exit(1)

    command = sys.argv[1]
    dir_path = Path(DATA_DIR)

    if command == "generate":
        if len(sys.argv) > 2:
            dir_path = Path(sys.argv[2])

        print(f"Generating checksums for: {dir_path}")
        checksums = generate_checksums(dir_path, recursive=True)

        output_path = dir_path / "checksums.json"
        save_checksums(checksums, output_path)
        print(f"Saved {len(checksums)} checksums to {output_path}")

    elif command == "verify":
        if len(sys.argv) > 2:
            dir_path = Path(sys.argv[2])

        checksum_file = dir_path / "checksums.json"
        if not checksum_file.exists():
            print(f"Error: Checksum file not found: {checksum_file}")
            sys.exit(1)

        checksums = load_checksums(checksum_file)
        print(f"Verifying {len(checksums)} files in: {dir_path}")

        if verify_checksums(dir_path, checksums, verbose=True):
            print("\n✓ All files verified successfully")
            sys.exit(0)
        else:
            print("\n✗ Verification failed: some files are missing or modified")
            sys.exit(1)

    elif command == "verify-file":
        if len(sys.argv) < 3:
            print("Usage: python -m data.checksum verify-file <file_path>")
            sys.exit(1)

        file_path = Path(sys.argv[2])
        checksum_file = DATA_DIR / "checksums.json"

        if not checksum_file.exists():
            print(f"Error: Checksum file not found: {checksum_file}")
            sys.exit(1)

        checksums = load_checksums(checksum_file)
        rel_path = str(file_path.relative_to(DATA_DIR))

        if rel_path not in checksums:
            print(f"Error: File not in checksum manifest: {rel_path}")
            sys.exit(1)

        actual = compute_sha256(file_path)
        expected = checksums[rel_path]

        if actual == expected:
            print(f"✓ {rel_path}: OK")
            sys.exit(0)
        else:
            print(f"✗ {rel_path}: MISMATCH")
            print(f"  Expected: {expected}")
            print(f"  Actual:   {actual}")
            sys.exit(1)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()