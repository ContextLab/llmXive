import os
import hashlib
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, List
import json

logger = logging.getLogger(__name__)

def compute_sha256(file_path: Path) -> str:
    """
    Computes the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file.

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
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise

def archive_data(source_dir: Path, archive_dir: Path, overwrite: bool = False) -> int:
    """
    Copies files from source_dir to archive_dir, preserving relative structure.

    Args:
        source_dir: Source directory containing files to archive.
        archive_dir: Destination directory for the archive.
        overwrite: If True, overwrite existing files in archive. If False, skip existing.

    Returns:
        Number of files successfully copied.
    """
    if not source_dir.exists():
        logger.error(f"Source directory does not exist: {source_dir}")
        return 0

    if not source_dir.is_dir():
        logger.error(f"Source path is not a directory: {source_dir}")
        return 0

    files_copied = 0
    source_dir = source_dir.resolve()
    archive_dir = archive_dir.resolve()

    for file_path in source_dir.rglob("*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(source_dir)
            dest_path = archive_dir / relative_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            if dest_path.exists() and not overwrite:
                logger.debug(f"Skipping existing file: {dest_path}")
                continue

            try:
                shutil.copy2(file_path, dest_path)
                files_copied += 1
                logger.debug(f"Copied: {file_path} -> {dest_path}")
            except Exception as e:
                logger.error(f"Failed to copy {file_path}: {e}")

    return files_copied

def verify_archive_integrity(archive_dir: Path, manifest_path: Path) -> bool:
    """
    Verifies the integrity of archived files against a checksum manifest.

    Args:
        archive_dir: Root directory of the archive.
        manifest_path: Path to the JSON manifest containing checksums.

    Returns:
        True if all files match checksums, False otherwise.
    """
    if not manifest_path.exists():
        logger.error(f"Manifest file not found: {manifest_path}")
        return False

    try:
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in manifest: {e}")
        return False

    archive_dir = archive_dir.resolve()
    all_valid = True

    for file_entry in manifest.get("files", []):
        rel_path = file_entry.get("path")
        expected_hash = file_entry.get("sha256")

        if not rel_path or not expected_hash:
            logger.warning("Invalid entry in manifest, skipping.")
            continue

        full_path = archive_dir / rel_path

        if not full_path.exists():
            logger.error(f"Missing file in archive: {full_path}")
            all_valid = False
            continue

        try:
            actual_hash = compute_sha256(full_path)
            if actual_hash != expected_hash:
                logger.error(f"Checksum mismatch for {full_path}: expected {expected_hash}, got {actual_hash}")
                all_valid = False
            else:
                logger.debug(f"Checksum verified: {full_path}")
        except Exception as e:
            logger.error(f"Error verifying checksum for {full_path}: {e}")
            all_valid = False

    return all_valid

def generate_checksum_manifest(archive_dir: Path, output_path: Path) -> Dict[str, Any]:
    """
    Scans an archive directory and generates a JSON manifest of SHA-256 checksums.

    Args:
        archive_dir: Root directory of the archive to scan.
        output_path: Path where the manifest JSON will be written.

    Returns:
        The generated manifest dictionary.
    """
    if not archive_dir.exists():
        raise FileNotFoundError(f"Archive directory not found: {archive_dir}")

    manifest = {
        "archive_root": str(archive_dir),
        "files": []
    }

    archive_dir = archive_dir.resolve()

    for file_path in archive_dir.rglob("*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(archive_dir)
            try:
                checksum = compute_sha256(file_path)
                file_info = {
                    "path": str(relative_path),
                    "size_bytes": file_path.stat().st_size,
                    "sha256": checksum
                }
                manifest["files"].append(file_info)
                logger.info(f"Checksum generated: {relative_path} ({checksum})")
            except Exception as e:
                logger.error(f"Failed to checksum {file_path}: {e}")

    # Sort files by path for deterministic output
    manifest["files"].sort(key=lambda x: x["path"])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Checksum manifest written to {output_path}")
    return manifest
