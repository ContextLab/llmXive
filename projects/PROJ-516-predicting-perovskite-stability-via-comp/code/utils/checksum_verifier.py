"""
Checksum Verifier Module

Validates raw data integrity against source checksums using SHA-256.
This module is used by the data ingestion pipeline to ensure data
fidelity before processing.
"""
import hashlib
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, List

from .config_manager import get_api_key

logger = logging.getLogger(__name__)


class ChecksumError(Exception):
    """Raised when checksum validation fails."""
    pass


def compute_sha256(file_path: Path, chunk_size: int = 8192) -> str:
    """
    Compute the SHA-256 hash of a file in chunks.

    Args:
        file_path: Path to the file to hash.
        chunk_size: Size of chunks to read at a time.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for checksum: {file_path}")

    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def validate_checksum(
    file_path: Path,
    expected_checksum: str,
    algorithm: str = "sha256"
) -> Tuple[bool, str]:
    """
    Validate a file's checksum against an expected value.

    Args:
        file_path: Path to the file to validate.
        expected_checksum: The expected checksum string (hex).
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Tuple of (is_valid: bool, computed_checksum: str).

    Raises:
        ChecksumError: If validation fails or file is missing.
    """
    if not file_path.exists():
        raise ChecksumError(f"File missing for validation: {file_path}")

    if algorithm.lower() != "sha256":
        raise ChecksumError(f"Unsupported checksum algorithm: {algorithm}")

    computed = compute_sha256(file_path)
    is_valid = computed.lower() == expected_checksum.lower()

    if not is_valid:
        logger.error(
            "Checksum mismatch for %s. Expected: %s, Got: %s",
            file_path, expected_checksum, computed
        )
    else:
        logger.info("Checksum validated successfully for %s", file_path)

    return is_valid, computed


def verify_artifacts_from_manifest(
    manifest_path: Path,
    artifacts_dir: Path
) -> Dict[str, bool]:
    """
    Verify multiple artifacts against a manifest file.

    The manifest is expected to be a YAML or JSON file containing a mapping
    of relative file paths to their expected SHA-256 checksums.

    Example manifest format:
    ```yaml
    raw_data.csv: a1b2c3...
    metadata.json: d4e5f6...
    ```

    Args:
        manifest_path: Path to the manifest file.
        artifacts_dir: Base directory containing the artifacts.

    Returns:
        Dictionary mapping artifact names to validation status (True/False).
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    import yaml
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    results = {}
    for rel_path, expected_hash in manifest.items():
        full_path = artifacts_dir / rel_path
        try:
            is_valid, _ = validate_checksum(full_path, expected_hash)
            results[rel_path] = is_valid
        except ChecksumError as e:
            logger.error(str(e))
            results[rel_path] = False
        except FileNotFoundError:
            logger.error(f"Artifact not found: {full_path}")
            results[rel_path] = False

    return results


def generate_checksum_manifest(
    artifacts_dir: Path,
    output_path: Path,
    recursive: bool = False
) -> None:
    """
    Generate a checksum manifest for all files in a directory.

    Args:
        artifacts_dir: Directory to scan for files.
        output_path: Path where the manifest YAML will be written.
        recursive: If True, scan subdirectories.
    """
    import yaml

    if not artifacts_dir.exists():
        raise FileNotFoundError(f"Directory not found: {artifacts_dir}")

    manifest = {}
    search_iter = artifacts_dir.rglob("*") if recursive else artifacts_dir.iterdir()

    for file_path in search_iter:
        if file_path.is_file():
            rel_path = file_path.relative_to(artifacts_dir)
            checksum = compute_sha256(file_path)
            manifest[str(rel_path)] = checksum

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(manifest, f, default_flow_style=False, sort_keys=True)

    logger.info("Checksum manifest written to %s", output_path)