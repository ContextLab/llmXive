"""
Directory setup and checksum utility for the molecular flexibility project.

This module provides functions to:
1. Create the required directory structure (data/raw, data/processed).
2. Compute SHA-256 checksums for data files.
3. Generate a manifest of checksums for data integrity verification.
"""
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict

# Import logging utilities from the project's utils
from utils.logging import get_logger, configure_root_logger
from utils.config import get_project_root

logger = get_logger(__name__)


def create_directories() -> Dict[str, Path]:
    """
    Create the standard directory structure for the project.

    Returns:
        Dict[str, Path]: A dictionary mapping directory names to their Path objects.
    """
    project_root = get_project_root()
    data_root = project_root / "data"

    directories = {
        "raw": data_root / "raw",
        "processed": data_root / "processed",
        "figures": data_root / "figures",
    }

    for name, path in directories.items():
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {path}")
        else:
            logger.debug(f"Directory already exists: {path}")

    return directories


def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file.

    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        str: The hexadecimal digest of the file.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_func = hashlib.new(algorithm)
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b""):
                hash_func.update(chunk)
    except IOError as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise

    return hash_func.hexdigest()


def generate_checksum_manifest(
    directory: Path,
    output_path: Optional[Path] = None,
    recursive: bool = True
) -> Dict[str, str]:
    """
    Generate a manifest of checksums for all files in a directory.

    Args:
        directory: The directory to scan.
        output_path: Optional path to write the JSON manifest.
        recursive: Whether to scan subdirectories.

    Returns:
        Dict[str, str]: A dictionary mapping relative file paths to their checksums.
    """
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    manifest = {}
    files: List[Path] = []

    if recursive:
        files = list(directory.rglob("*"))
    else:
        files = list(directory.iterdir())

    # Filter for files only
    files = [f for f in files if f.is_file()]

    logger.info(f"Scanning {len(files)} files in {directory}...")

    for file_path in files:
        try:
            # Use relative path from the target directory for the manifest
            rel_path = file_path.relative_to(directory)
            checksum = compute_file_checksum(file_path)
            manifest[str(rel_path)] = checksum
            logger.debug(f"Checksummed: {rel_path} -> {checksum[:16]}...")
        except Exception as e:
            logger.warning(f"Failed to checksum {file_path}: {e}")

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Manifest written to: {output_path}")

    return manifest


def main() -> int:
    """
    Main entry point for the directory setup and checksum utility.

    This function:
    1. Creates the required directory structure.
    2. Generates a checksum manifest for the 'data' directory if it contains files.
    3. Prints the results to the console.

    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    configure_root_logger()
    logger.info("Starting directory setup and checksum generation...")

    try:
        # 1. Create directories
        dirs = create_directories()
        logger.info(f"Directory structure ready: {list(dirs.keys())}")

        # 2. Generate manifest for the data root if files exist
        data_root = dirs["raw"].parent
        manifest_path = data_root / "checksum_manifest.json"

        # Check if there are any files to checksum
        has_files = any(data_root.rglob("*"))
        if has_files:
            logger.info("Generating checksum manifest for data directory...")
            manifest = generate_checksum_manifest(data_root, output_path=manifest_path)
            logger.info(f"Manifest contains {len(manifest)} entries.")
        else:
            logger.info("No files found in data directory. Skipping manifest generation.")
            # Create an empty manifest if the directory is new
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=2)
            logger.info(f"Created empty manifest at: {manifest_path}")

        logger.info("Setup complete.")
        return 0

    except Exception as e:
        logger.error(f"Setup failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
