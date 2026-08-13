"""
Artifact hashing utilities for the llmXive pipeline.
Generates SHA-256 checksums for all intermediate and final files to ensure
reproducibility and data integrity.
"""
import hashlib
import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger


def calculate_sha256(file_path: str | Path, chunk_size: int = 8192) -> str:
    """
    Calculate the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.
        chunk_size: Size of chunks to read at a time (default 8KB).

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If the path is a directory.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if file_path.is_dir():
        raise IsADirectoryError(f"Path is a directory, not a file: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(chunk)
    except IOError as e:
        logger.error(f"Failed to read file for hashing {file_path}: {e}")
        raise

    return sha256_hash.hexdigest()


def generate_manifest(
    file_paths: List[str | Path],
    output_path: Optional[str | Path] = None,
    base_dir: Optional[str | Path] = None
) -> Dict[str, str]:
    """
    Generate a manifest of SHA-256 hashes for a list of files.

    Args:
        file_paths: List of file paths to hash.
        output_path: Optional path to write the JSON manifest file.
        base_dir: Optional base directory to resolve relative paths against.

    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes.

    Raises:
        FileNotFoundError: If any file in the list does not exist.
    """
    manifest = {}
    base = Path(base_dir) if base_dir else Path.cwd()

    logger.info(f"Generating manifest for {len(file_paths)} files...")

    for path in file_paths:
        p = Path(path)
        # Resolve relative to base_dir if provided, else relative to current working dir
        if not p.is_absolute():
            if base_dir:
                p = (Path(base_dir) / p).resolve()
            else:
                p = p.resolve()

        if not p.exists():
            logger.warning(f"File not found, skipping: {p}")
            continue

        try:
            file_hash = calculate_sha256(p)
            # Store path relative to base_dir for portability
            relative_path = str(p.relative_to(base))
            manifest[relative_path] = file_hash
            logger.debug(f"Hashed {relative_path}: {file_hash[:16]}...")
        except Exception as e:
            logger.error(f"Failed to hash {p}: {e}")
            raise

    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Manifest written to {output_file}")

    return manifest


def verify_manifest(manifest_path: str | Path, base_dir: Optional[str | Path] = None) -> bool:
    """
    Verify files against a previously generated manifest.

    Args:
        manifest_path: Path to the JSON manifest file.
        base_dir: Base directory to resolve paths within the manifest.

    Returns:
        True if all files match their hashes, False otherwise.
    """
    manifest_file = Path(manifest_path)
    if not manifest_file.exists():
        logger.error(f"Manifest file not found: {manifest_path}")
        return False

    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    base = Path(base_dir) if base_dir else manifest_file.parent
    all_valid = True

    for rel_path, expected_hash in manifest.items():
        full_path = base / rel_path
        if not full_path.exists():
            logger.error(f"Missing file during verification: {full_path}")
            all_valid = False
            continue

        try:
            actual_hash = calculate_sha256(full_path)
            if actual_hash != expected_hash:
                logger.error(f"Hash mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}")
                all_valid = False
            else:
                logger.debug(f"Verified {rel_path}")
        except Exception as e:
            logger.error(f"Error verifying {full_path}: {e}")
            all_valid = False

    if all_valid:
        logger.info("All files verified successfully.")
    else:
        logger.warning("Verification failed: some files did not match or were missing.")

    return all_valid
