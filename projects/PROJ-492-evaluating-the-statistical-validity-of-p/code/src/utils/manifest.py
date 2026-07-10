"""
Manifest generation utility for FR-024.

Generates a manifest.json file containing SHA256 content hashes for all
specified artifacts in the output and data directories.
"""
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

from code.src.utils.logger import get_default_logger, AuditLogger

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
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hasher = hashlib.new(algorithm)
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")

    return hasher.hexdigest()

def collect_files_to_hash(
    base_dir: Path,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
) -> List[Path]:
    """
    Collect all files to be included in the manifest.

    Args:
        base_dir: Base directory to scan.
        include_patterns: List of glob patterns to include (default: all files).
        exclude_patterns: List of glob patterns to exclude (default: none).

    Returns:
        List of Path objects for files to hash.
    """
    if include_patterns is None:
        include_patterns = ["**/*"]

    all_files: List[Path] = []
    for pattern in include_patterns:
        all_files.extend(base_dir.glob(pattern))

    # Filter to only files
    all_files = [f for f in all_files if f.is_file()]

    # Apply exclusion patterns
    if exclude_patterns:
        filtered_files = []
        for f in all_files:
            rel_path = f.relative_to(base_dir)
            if not any(
                str(rel_path).glob(exclude_pattern) for exclude_pattern in exclude_patterns
            ):
                filtered_files.append(f)
        all_files = filtered_files

    return sorted(all_files)

def generate_manifest(
    output_dir: Path,
    manifest_path: Optional[Path] = None,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    logger: Optional[AuditLogger] = None,
) -> Dict[str, Any]:
    """
    Generate a manifest.json file with SHA256 hashes for all artifacts.

    Args:
        output_dir: Directory containing the artifacts to hash.
        manifest_path: Path where the manifest.json will be written.
                       Defaults to {output_dir}/manifest.json.
        include_patterns: Glob patterns for files to include.
        exclude_patterns: Glob patterns for files to exclude.
        logger: Optional logger instance.

    Returns:
        The manifest dictionary.
    """
    if logger is None:
        logger = get_default_logger()

    if manifest_path is None:
        manifest_path = output_dir / "manifest.json"

    logger.info(f"Generating manifest for directory: {output_dir}")

    if not output_dir.exists():
        logger.error(f"Output directory does not exist: {output_dir}")
        raise FileNotFoundError(f"Output directory not found: {output_dir}")

    files = collect_files_to_hash(output_dir, include_patterns, exclude_patterns)

    logger.info(f"Found {len(files)} files to hash")

    manifest: Dict[str, Any] = {
        "version": "1.0.0",
        "generated_at": "",  # Will be set by caller if needed
        "base_directory": str(output_dir),
        "files": {},
        "total_files": len(files),
    }

    for file_path in files:
        try:
            rel_path = file_path.relative_to(output_dir)
            file_hash = compute_file_hash(file_path)
            manifest["files"][str(rel_path)] = {
                "sha256": file_hash,
                "size_bytes": file_path.stat().st_size,
            }
            logger.debug(f"Hashed: {rel_path} -> {file_hash[:16]}...")
        except (FileNotFoundError, IOError) as e:
            logger.warning(f"Skipping file {file_path}: {e}")

    # Write manifest to file
    try:
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Manifest written to: {manifest_path}")
    except IOError as e:
        logger.error(f"Failed to write manifest: {e}")
        raise

    return manifest

def verify_manifest(
    manifest_path: Path,
    base_dir: Optional[Path] = None,
    logger: Optional[AuditLogger] = None,
) -> bool:
    """
    Verify that all files in a manifest match their recorded hashes.

    Args:
        manifest_path: Path to the manifest.json file.
        base_dir: Base directory for file paths. Defaults to manifest's base_directory.
        logger: Optional logger instance.

    Returns:
        True if all hashes match, False otherwise.
    """
    if logger is None:
        logger = get_default_logger()

    if not manifest_path.exists():
        logger.error(f"Manifest file not found: {manifest_path}")
        return False

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    base_directory = Path(manifest.get("base_directory", str(manifest_path.parent)))
    if base_dir:
        base_directory = base_dir

    all_valid = True
    total_files = manifest.get("total_files", 0)
    verified_files = 0

    for rel_path, file_info in manifest.get("files", {}).items():
        file_path = base_directory / rel_path
        expected_hash = file_info.get("sha256")

        if not file_path.exists():
            logger.error(f"File missing: {rel_path}")
            all_valid = False
            continue

        try:
            actual_hash = compute_file_hash(file_path)
            if actual_hash != expected_hash:
                logger.error(f"Hash mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}")
                all_valid = False
            else:
                verified_files += 1
        except (FileNotFoundError, IOError) as e:
            logger.error(f"Error verifying {rel_path}: {e}")
            all_valid = False

    logger.info(f"Verification complete: {verified_files}/{total_files} files valid")
    return all_valid

def main():
    """Command-line entry point for manifest generation."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate or verify manifest.json with SHA256 hashes")
    parser.add_argument(
        "command",
        choices=["generate", "verify"],
        help="Command to execute: generate or verify",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Output directory containing artifacts (for generate) or base directory (for verify)",
    )
    parser.add_argument(
        "--manifest-path",
        type=Path,
        default=None,
        help="Path to manifest.json (defaults to output/manifest.json)",
    )
    parser.add_argument(
        "--include",
        nargs="+",
        default=["**/*"],
        help="Glob patterns for files to include",
    )
    parser.add_argument(
        "--exclude",
        nargs="+",
        default=["**/.git/**", "**/__pycache__/**", "**/*.pyc"],
        help="Glob patterns for files to exclude",
    )

    args = parser.parse_args()
    logger = get_default_logger()

    try:
        if args.command == "generate":
            manifest = generate_manifest(
                output_dir=args.output_dir,
                manifest_path=args.manifest_path,
                include_patterns=args.include,
                exclude_patterns=args.exclude,
                logger=logger,
            )
            print(f"Manifest generated successfully: {args.manifest_path or args.output_dir / 'manifest.json'}")
            print(f"Total files: {manifest['total_files']}")
            return 0
        elif args.command == "verify":
            manifest_path = args.manifest_path or args.output_dir / "manifest.json"
            is_valid = verify_manifest(
                manifest_path=manifest_path,
                base_dir=args.output_dir,
                logger=logger,
            )
            if is_valid:
                print("All hashes verified successfully.")
                return 0
            else:
                print("Hash verification failed. Check logs for details.")
                return 1
    except Exception as e:
        logger.error(f"Command failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
