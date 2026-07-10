"""
Manifest generation utility for FR-024.
Generates manifest.json with SHA256 hashes for all files in specified directories.
"""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from code.src.utils.logger import get_default_logger


def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the SHA256 hash of a file's contents.

    Args:
        file_path: Path to the file to hash.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal string of the hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    hasher = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def scan_directory(
    base_dir: Path,
    extensions: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None
) -> List[Path]:
    """
    Scan a directory recursively for files matching criteria.

    Args:
        base_dir: Root directory to scan.
        extensions: List of file extensions to include (e.g., ['.json', '.csv']).
                   If None, include all files.
        exclude_patterns: List of path patterns to exclude (e.g., ['__pycache__', '.git']).

    Returns:
        List of Path objects for matching files.
    """
    files = []
    exclude_patterns = exclude_patterns or []
    extensions = extensions or []

    for file_path in base_dir.rglob("*"):
        if not file_path.is_file():
            continue

        # Check extensions
        if extensions:
            if file_path.suffix not in extensions:
                continue

        # Check exclusion patterns
        excluded = False
        for pattern in exclude_patterns:
            if pattern in str(file_path):
                excluded = True
                break
        if excluded:
            continue

        files.append(file_path)

    return sorted(files)


def generate_manifest(
    target_dirs: List[Path],
    output_path: Path,
    extensions: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """
    Generate a manifest.json file with SHA256 hashes for all files in target directories.

    Args:
        target_dirs: List of directories to scan for files.
        output_path: Path where manifest.json will be written.
        extensions: List of file extensions to include.
        exclude_patterns: List of path patterns to exclude.
        logger: Optional logger instance.

    Returns:
        Dictionary containing the manifest data.

    Raises:
        ValueError: If target_dirs is empty or no files are found.
        IOError: If output_path cannot be written.
    """
    if not logger:
        logger = get_default_logger()

    logger.info(f"Generating manifest for directories: {target_dirs}")

    all_files: List[Path] = []
    for target_dir in target_dirs:
        if not target_dir.exists():
            logger.warning(f"Target directory does not exist: {target_dir}")
            continue
        files = scan_directory(target_dir, extensions, exclude_patterns)
        all_files.extend(files)

    if not all_files:
        raise ValueError("No files found to include in manifest")

    logger.info(f"Found {len(all_files)} files to hash")

    manifest = {
        "version": "1.0",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "algorithm": "sha256",
        "files": {}
    }

    for file_path in all_files:
        try:
            file_hash = compute_file_hash(file_path)
            # Store relative path from project root (assuming project root is parent of 'code')
            relative_path = file_path.relative_to(file_path.parent.parent.parent)
            manifest["files"][str(relative_path)] = file_hash
            logger.debug(f"Hashed: {relative_path} -> {file_hash[:16]}...")
        except Exception as e:
            logger.error(f"Failed to hash file {file_path}: {e}")
            raise

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write manifest
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Manifest written to {output_path} with {len(manifest['files'])} entries")
    return manifest


def validate_manifest(
    manifest_path: Path,
    base_dir: Path,
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Validate that file hashes in a manifest match current file contents.

    Args:
        manifest_path: Path to the manifest.json file.
        base_dir: Base directory to resolve file paths against.
        logger: Optional logger instance.

    Returns:
        True if all hashes match, False otherwise.
    """
    if not logger:
        logger = get_default_logger()

    if not manifest_path.exists():
        logger.error(f"Manifest file not found: {manifest_path}")
        return False

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    all_valid = True
    for relative_path, expected_hash in manifest.get("files", {}).items():
        full_path = base_dir / relative_path
        if not full_path.exists():
            logger.warning(f"File missing: {relative_path}")
            all_valid = False
            continue

        try:
            actual_hash = compute_file_hash(full_path)
            if actual_hash != expected_hash:
                logger.error(f"Hash mismatch for {relative_path}")
                logger.error(f"  Expected: {expected_hash}")
                logger.error(f"  Actual:   {actual_hash}")
                all_valid = False
            else:
                logger.debug(f"Hash verified: {relative_path}")
        except Exception as e:
            logger.error(f"Error validating {relative_path}: {e}")
            all_valid = False

    return all_valid


def main():
    """CLI entry point for manifest generation."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Generate manifest.json with SHA256 hashes for project artifacts."
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("output/manifest.json"),
        help="Output path for manifest.json (default: output/manifest.json)"
    )
    parser.add_argument(
        "--dirs", "-d",
        type=Path,
        nargs="+",
        default=[Path("output"), Path("data/processed")],
        help="Directories to scan for files (default: output data/processed)"
    )
    parser.add_argument(
        "--extensions", "-e",
        type=str,
        nargs="+",
        default=None,
        help="File extensions to include (e.g., .json .csv). Default: all files."
    )
    parser.add_argument(
        "--exclude",
        type=str,
        nargs="+",
        default=["__pycache__", ".git", "*.pyc"],
        help="Patterns to exclude from scanning."
    )
    parser.add_argument(
        "--validate", "-v",
        action="store_true",
        help="Validate existing manifest instead of generating a new one."
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path("."),
        help="Base directory for validation (default: current directory)"
    )

    args = parser.parse_args()
    logger = get_default_logger()

    try:
        if args.validate:
            if not args.output.exists():
                logger.error(f"Manifest file not found: {args.output}")
                sys.exit(1)
            is_valid = validate_manifest(args.output, args.base_dir, logger)
            if is_valid:
                logger.info("Manifest validation PASSED: All hashes match.")
                sys.exit(0)
            else:
                logger.error("Manifest validation FAILED: Hash mismatches detected.")
                sys.exit(1)
        else:
            manifest = generate_manifest(
                target_dirs=args.dirs,
                output_path=args.output,
                extensions=args.extensions,
                exclude_patterns=args.exclude,
                logger=logger
            )
            logger.info(f"Manifest generated successfully with {len(manifest['files'])} files.")
            sys.exit(0)
    except Exception as e:
        logger.error(f"Manifest generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
