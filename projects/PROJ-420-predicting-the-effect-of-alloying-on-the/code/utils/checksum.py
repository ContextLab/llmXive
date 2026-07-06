"""
Checksum utilities for verifying data integrity.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from config import get_config
from logging_config import get_logger

logger = get_logger(__name__)


def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal checksum string.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hasher = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def verify_file_checksum(file_path: Path, expected_checksum: str, algorithm: str = "sha256") -> bool:
    """
    Verify a file's checksum against an expected value.

    Args:
        file_path: Path to the file.
        expected_checksum: Expected checksum string.
        algorithm: Hash algorithm to use.

    Returns:
        True if checksum matches, False otherwise.
    """
    try:
        actual_checksum = compute_file_checksum(file_path, algorithm)
        return actual_checksum.lower() == expected_checksum.lower()
    except Exception as e:
        logger.error(f"Error verifying checksum for {file_path}: {e}")
        return False


def generate_checksum_manifest(data_dir: Path, output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Generate a manifest of checksums for all files in a directory.

    Args:
        data_dir: Directory to scan.
        output_path: Optional path to save the manifest JSON.

    Returns:
        Dictionary mapping relative file paths to their checksums.
    """
    if not data_dir.exists():
        raise FileNotFoundError(f"Directory not found: {data_dir}")

    manifest = {
        "algorithm": "sha256",
        "files": {}
    }

    for root, _, files in os.walk(data_dir):
        for filename in files:
            if filename.endswith(".checksum"):
                continue  # Skip existing checksum files

            file_path = Path(root) / filename
            relative_path = file_path.relative_to(data_dir)

            try:
                checksum = compute_file_checksum(file_path)
                manifest["files"][str(relative_path)] = checksum
                logger.debug(f"Computed checksum for {relative_path}")
            except Exception as e:
                logger.warning(f"Failed to compute checksum for {relative_path}: {e}")

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Checksum manifest saved to {output_path}")

    return manifest


def verify_checksum_manifest(manifest_path: Path, data_dir: Optional[Path] = None) -> Dict[str, bool]:
    """
    Verify all files against a checksum manifest.

    Args:
        manifest_path: Path to the manifest JSON.
        data_dir: Base directory for file paths (defaults to manifest's parent).

    Returns:
        Dictionary mapping file paths to verification status (True/False).
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    if data_dir is None:
        data_dir = manifest_path.parent

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    results = {}
    algorithm = manifest.get("algorithm", "sha256")

    for relative_path, expected_checksum in manifest.get("files", {}).items():
        file_path = data_dir / relative_path
        if file_path.exists():
            is_valid = verify_file_checksum(file_path, expected_checksum, algorithm)
            results[relative_path] = is_valid
            status = "OK" if is_valid else "MISMATCH"
            logger.info(f"{relative_path}: {status}")
        else:
            results[relative_path] = False
            logger.warning(f"{relative_path}: FILE NOT FOUND")

    return results


def get_data_checksums() -> Dict[str, str]:
    """
    Get checksums for all critical data files in the project.

    Returns:
        Dictionary mapping file names to checksums.
    """
    config = get_config()
    data_dir = config.data_dir
    checksums = {}

    # Check raw data
    raw_dir = data_dir / "raw"
    if raw_dir.exists():
        for file in raw_dir.glob("*"):
            if file.is_file():
                checksums[file.name] = compute_file_checksum(file)

    # Check processed data
    proc_dir = data_dir / "processed"
    if proc_dir.exists():
        for file in proc_dir.glob("*"):
            if file.is_file():
                checksums[file.name] = compute_file_checksum(file)

    return checksums