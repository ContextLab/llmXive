import hashlib
import os
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, List
import json

from config import get_project_root

logger = logging.getLogger(__name__)

CHECKSUMS_FILE_NAME = "checksums.txt"
CHECKSUMS_JSON_FILE_NAME = "checksums_manifest.json"

def compute_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use ('md5', 'sha256').

    Returns:
        Hexadecimal checksum string.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if algorithm == "md5":
        hasher = hashlib.md5()
    elif algorithm == "sha256":
        hasher = hashlib.sha256()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}. Use 'md5' or 'sha256'.")

    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except PermissionError:
        raise PermissionError(f"Permission denied reading file: {file_path}")
    except Exception as e:
        raise RuntimeError(f"Error computing checksum for {file_path}: {e}")

def generate_checksums(target_files: List[Path], output_path: Path, algorithm: str = "sha256") -> Dict[str, str]:
    """
    Generate checksums for a list of files and write them to a file.

    Args:
        target_files: List of file paths to checksum.
        output_path: Path to the output checksums file.
        algorithm: Hash algorithm to use.

    Returns:
        Dictionary mapping file names to checksums.
    """
    checksums = {}
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Generating {algorithm} checksums for {len(target_files)} files...")

    with open(output_path, "w") as f:
        for file_path in target_files:
            if not file_path.exists():
                logger.warning(f"Skipping non-existent file: {file_path}")
                continue

            try:
                checksum = compute_checksum(file_path, algorithm)
                # Store relative path from project root for portability
                rel_path = file_path.relative_to(get_project_root())
                checksums[str(rel_path)] = checksum
                f.write(f"{checksum}  {rel_path}\n")
                logger.debug(f"Checksum computed for {rel_path}: {checksum}")
            except Exception as e:
                logger.error(f"Failed to compute checksum for {file_path}: {e}")

    # Also save a JSON manifest for programmatic access
    json_path = output_path.with_suffix(".json")
    with open(json_path, "w") as f:
        json.dump(checksums, f, indent=2)

    logger.info(f"Checksums written to {output_path} and {json_path}")
    return checksums

def verify_checksums(checksums_path: Path, algorithm: str = "sha256") -> Tuple[bool, List[str], List[str]]:
    """
    Verify files against a checksums file.

    Args:
        checksums_path: Path to the checksums file.
        algorithm: Hash algorithm to use.

    Returns:
        Tuple of (all_valid, list_of_passed_files, list_of_failed_files).
    """
    if not checksums_path.exists():
        raise FileNotFoundError(f"Checksums file not found: {checksums_path}")

    project_root = get_project_root()
    passed = []
    failed = []

    logger.info(f"Verifying checksums from {checksums_path}...")

    with open(checksums_path, "r") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        parts = line.split("  ", 1)
        if len(parts) != 2:
            logger.warning(f"Malformed checksum line: {line}")
            continue

        expected_checksum, rel_path = parts
        file_path = project_root / rel_path

        if not file_path.exists():
            logger.error(f"File missing during verification: {file_path}")
            failed.append(rel_path)
            continue

        try:
            actual_checksum = compute_checksum(file_path, algorithm)
            if actual_checksum == expected_checksum:
                passed.append(rel_path)
                logger.debug(f"Verified: {rel_path}")
            else:
                logger.error(f"Checksum mismatch for {rel_path}: expected {expected_checksum}, got {actual_checksum}")
                failed.append(rel_path)
        except Exception as e:
            logger.error(f"Error verifying {file_path}: {e}")
            failed.append(rel_path)

    all_valid = len(failed) == 0
    if all_valid:
        logger.info("All checksums verified successfully.")
    else:
        logger.error(f"Verification failed for {len(failed)} files.")

    return all_valid, passed, failed

def update_checksum_for_file(file_path: Path, checksums_path: Path, algorithm: str = "sha256") -> bool:
    """
    Update the checksum for a specific file in the checksums file.
    If the file is not in the list, it is appended.

    Args:
        file_path: Path to the file to update.
        checksums_path: Path to the checksums file.
        algorithm: Hash algorithm to use.

    Returns:
        True if updated successfully, False otherwise.
    """
    if not file_path.exists():
        logger.error(f"Cannot update checksum for non-existent file: {file_path}")
        return False

    try:
        new_checksum = compute_checksum(file_path, algorithm)
    except Exception as e:
        logger.error(f"Failed to compute new checksum: {e}")
        return False

    project_root = get_project_root()
    rel_path = str(file_path.relative_to(project_root))

    # Read existing checksums
    checksums = {}
    if checksums_path.exists():
        with open(checksums_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split("  ", 1)
                if len(parts) == 2:
                    checksums[parts[1]] = parts[0]

    # Update or add
    checksums[rel_path] = new_checksum

    # Write back
    with open(checksums_path, "w") as f:
        for path, checksum in checksums.items():
            f.write(f"{checksum}  {path}\n")

    logger.info(f"Updated checksum for {rel_path} in {checksums_path}")
    return True

def main():
    """CLI entry point for checksum utilities."""
    import argparse

    parser = argparse.ArgumentParser(description="Checksum verification utility")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate checksums for files")
    gen_parser.add_argument("files", nargs="+", help="Files to checksum")
    gen_parser.add_argument("-o", "--output", default="artifacts/checksums.txt", help="Output file path")
    gen_parser.add_argument("-a", "--algorithm", choices=["md5", "sha256"], default="sha256", help="Hash algorithm")

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify files against checksums")
    verify_parser.add_argument("-c", "--checksums", default="artifacts/checksums.txt", help="Checksums file path")
    verify_parser.add_argument("-a", "--algorithm", choices=["md5", "sha256"], default="sha256", help="Hash algorithm")

    # Update command
    update_parser = subparsers.add_parser("update", help="Update checksum for a specific file")
    update_parser.add_argument("file", help="File to update")
    update_parser.add_argument("-c", "--checksums", default="artifacts/checksums.txt", help="Checksums file path")
    update_parser.add_argument("-a", "--algorithm", choices=["md5", "sha256"], default="sha256", help="Hash algorithm")

    args = parser.parse_args()

    if args.command == "generate":
        files = [Path(f) for f in args.files]
        output = Path(args.output)
        generate_checksums(files, output, args.algorithm)
    elif args.command == "verify":
        checksums_path = Path(args.checksums)
        valid, passed, failed = verify_checksums(checksums_path, args.algorithm)
        if not valid:
            print(f"Verification failed. Passed: {len(passed)}, Failed: {len(failed)}")
            for f in failed:
                print(f"  - {f}")
            exit(1)
        else:
            print("All checksums verified.")
    elif args.command == "update":
        file_path = Path(args.file)
        checksums_path = Path(args.checksums)
        success = update_checksum_for_file(file_path, checksums_path, args.algorithm)
        if not success:
            exit(1)
    else:
        parser.print_help()
        exit(1)

if __name__ == "__main__":
    main()
