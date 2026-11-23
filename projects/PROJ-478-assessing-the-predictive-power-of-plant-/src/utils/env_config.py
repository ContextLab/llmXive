"""
Environment configuration management and checksum verification for raw downloads.

This module handles:
1. Loading environment configuration from YAML/JSON files.
2. Computing SHA-256 checksums for downloaded files.
3. Verifying file integrity against registered checksums.
4. Managing a manifest of verified downloads.
"""
import os
import hashlib
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    import yaml
except ImportError:
    yaml = None

from src.utils.logging import get_logger

# Constants
CHECKSUM_ALGORITHM = "sha256"
MANIFEST_FILENAME = "download_manifest.json"
CONFIG_FILENAMES = ["config.yaml", "config.yml", "config.json"]

logger = get_logger(__name__)


def load_environment_config(config_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load environment configuration from a YAML or JSON file in the specified directory.

    Searches for config files in the following order:
    1. config.yaml
    2. config.yml
    3. config.json

    Args:
        config_dir: Directory to search for config file. Defaults to project root.

    Returns:
        Dictionary containing configuration values.

    Raises:
        FileNotFoundError: If no config file is found.
        ValueError: If config file is invalid.
    """
    if config_dir is None:
        config_dir = Path.cwd()

    config = {}

    for filename in CONFIG_FILENAMES:
        config_path = config_dir / filename
        if config_path.exists():
            logger.info(f"Loading configuration from {config_path}")
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    if filename.endswith('.json'):
                        config = json.load(f)
                    elif yaml is not None:
                        config = yaml.safe_load(f)
                    else:
                        raise ImportError("PyYAML is required to load YAML config files")
            except (json.JSONDecodeError, yaml.YAMLError) as e:
                raise ValueError(f"Invalid configuration file {config_path}: {e}")
            break

    if not config:
        raise FileNotFoundError(
            f"No configuration file found in {config_dir}. "
            f"Expected one of: {CONFIG_FILENAMES}"
        )

    logger.info(f"Configuration loaded successfully from {config_path}")
    return config


def compute_file_checksum(file_path: Path, algorithm: str = CHECKSUM_ALGORITHM) -> str:
    """
    Compute the checksum of a file using the specified algorithm.

    Args:
        file_path: Path to the file to compute checksum for.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal string of the file's checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If an unsupported algorithm is specified.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if algorithm not in hashlib.algorithms_available:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")

    hash_obj = hashlib.new(algorithm)

    logger.debug(f"Computing {algorithm} checksum for {file_path}")
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b''):
            hash_obj.update(chunk)

    checksum = hash_obj.hexdigest()
    logger.debug(f"Checksum computed: {checksum[:16]}...")
    return checksum


def verify_checksum(file_path: Path, expected_checksum: str, algorithm: str = CHECKSUM_ALGORITHM) -> bool:
    """
    Verify a file's checksum against an expected value.

    Args:
        file_path: Path to the file to verify.
        expected_checksum: Expected checksum value (hex string).
        algorithm: Hash algorithm to use.

    Returns:
        True if checksum matches, False otherwise.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    actual_checksum = compute_file_checksum(file_path, algorithm)

    if actual_checksum.lower() == expected_checksum.lower():
        logger.info(f"Checksum verified for {file_path.name}: {actual_checksum[:16]}...")
        return True
    else:
        logger.error(
            f"Checksum mismatch for {file_path.name}!\n"
            f"  Expected: {expected_checksum}\n"
            f"  Actual:   {actual_checksum}"
        )
        return False


def register_checksum(
    manifest_path: Path,
    file_path: Path,
    checksum: Optional[str] = None,
    algorithm: str = CHECKSUM_ALGORITHM
) -> Dict[str, Any]:
    """
    Register a file's checksum in the manifest.

    If checksum is not provided, it will be computed.

    Args:
        manifest_path: Path to the manifest file.
        file_path: Path to the file being registered.
        checksum: Pre-computed checksum (optional).
        algorithm: Hash algorithm to use.

    Returns:
        Updated manifest entry for the file.
    """
    if not manifest_path.parent.exists():
        manifest_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing manifest
    manifest = {}
    if manifest_path.exists():
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

    # Compute or use provided checksum
    if checksum is None:
        checksum = compute_file_checksum(file_path, algorithm)

    # Create or update entry
    relative_path = str(file_path.relative_to(manifest_path.parent.parent))
    entry = {
        "file_path": relative_path,
        "checksum": checksum,
        "algorithm": algorithm,
        "size_bytes": file_path.stat().st_size,
        "registered_at": str(Path.cwd())  # Could be improved with timestamp
    }

    manifest[relative_path] = entry

    # Save updated manifest
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Registered checksum for {relative_path}: {checksum[:16]}...")
    return entry


def verify_all_downloads(manifest_path: Optional[Path] = None) -> Dict[str, bool]:
    """
    Verify all files registered in the manifest.

    Args:
        manifest_path: Path to the manifest file. Defaults to data/raw/download_manifest.json.

    Returns:
        Dictionary mapping file paths to verification status (True/False).
    """
    if manifest_path is None:
        manifest_path = Path.cwd() / "data" / "raw" / MANIFEST_FILENAME

    if not manifest_path.exists():
        logger.warning(f"No manifest found at {manifest_path}. Nothing to verify.")
        return {}

    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    results = {}
    all_valid = True

    for relative_path, entry in manifest.items():
        file_path = Path.cwd() / relative_path

        if not file_path.exists():
            logger.error(f"File missing: {relative_path}")
            results[relative_path] = False
            all_valid = False
            continue

        expected_checksum = entry.get("checksum")
        algorithm = entry.get("algorithm", CHECKSUM_ALGORITHM)

        if expected_checksum is None:
            logger.warning(f"No checksum registered for {relative_path}")
            results[relative_path] = False
            all_valid = False
            continue

        is_valid = verify_checksum(file_path, expected_checksum, algorithm)
        results[relative_path] = is_valid

        if not is_valid:
            all_valid = False

    if all_valid:
        logger.info(f"All {len(manifest)} files verified successfully.")
    else:
        failed = [k for k, v in results.items() if not v]
        logger.warning(f"Verification failed for {len(failed)} files: {failed}")

    return results


def verify_download(
    file_path: Path,
    manifest_path: Optional[Path] = None
) -> bool:
    """
    Verify a single downloaded file against the manifest.

    Args:
        file_path: Path to the file to verify.
        manifest_path: Path to the manifest file.

    Returns:
        True if file exists and checksum matches, False otherwise.
    """
    if manifest_path is None:
        manifest_path = Path.cwd() / "data" / "raw" / MANIFEST_FILENAME

    if not manifest_path.exists():
        logger.warning(f"No manifest found at {manifest_path}")
        return False

    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    relative_path = str(file_path.relative_to(manifest_path.parent.parent))

    if relative_path not in manifest:
        logger.warning(f"No registration found for {relative_path} in manifest")
        return False

    expected_checksum = manifest[relative_path].get("checksum")
    if expected_checksum is None:
        logger.warning(f"No checksum registered for {relative_path}")
        return False

    return verify_checksum(file_path, expected_checksum)


def get_manifest_path() -> Path:
    """Get the default path for the download manifest."""
    return Path.cwd() / "data" / "raw" / MANIFEST_FILENAME
