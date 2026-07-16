"""
Utility functions for checksum generation and verification.
Supports SHA-256 for files in data/raw/ and data/processed/.
"""
import hashlib
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from config import get_path_env_override

# Configure logging
logger = logging.getLogger(__name__)

CHUNK_SIZE = 8192  # 8KB chunks for reading files


def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If the path is a directory.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if file_path.is_dir():
        raise IsADirectoryError(f"Path is a directory: {file_path}")

    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    """
    Verify the SHA-256 checksum of a file against an expected value.

    Args:
        file_path: Path to the file.
        expected_checksum: Expected SHA-256 hash string.

    Returns:
        True if the checksum matches, False otherwise.
    """
    try:
        actual_checksum = compute_sha256(file_path)
        match = actual_checksum.lower() == expected_checksum.lower()
        if not match:
            logger.warning(
                f"Checksum mismatch for {file_path}: "
                f"expected {expected_checksum}, got {actual_checksum}"
            )
        else:
            logger.info(f"Checksum verified for {file_path}")
        return match
    except (FileNotFoundError, IsADirectoryError) as e:
        logger.error(f"Error verifying checksum for {file_path}: {e}")
        return False


def scan_directory_for_checksums(
    base_dir: Path,
    extensions: Optional[list] = None
) -> Dict[str, str]:
    """
    Scan a directory recursively for files and compute their checksums.

    Args:
        base_dir: Root directory to scan.
        extensions: Optional list of file extensions to include (e.g., ['.h5', '.parquet']).
                   If None, all files are processed.

    Returns:
        Dictionary mapping relative file paths (from base_dir) to their SHA-256 checksums.
    """
    checksums = {}
    if not base_dir.exists():
        logger.warning(f"Directory does not exist: {base_dir}")
        return checksums

    for root, _, files in os.walk(base_dir):
        for file in files:
            file_path = Path(root) / file
            if extensions:
                if file_path.suffix.lower() not in [e.lower() for e in extensions]:
                    continue
            try:
                checksum = compute_sha256(file_path)
                rel_path = file_path.relative_to(base_dir)
                checksums[str(rel_path)] = checksum
            except (FileNotFoundError, IsADirectoryError) as e:
                logger.error(f"Skipped {file_path}: {e}")

    return checksums


def update_state_file_with_checksums(
    state_file_path: Path,
    checksums: Dict[str, str],
    source_dir_name: str
) -> None:
    """
    Append checksum information to the project state YAML file.

    Args:
        state_file_path: Path to the state YAML file.
        checksums: Dictionary of relative paths to checksums.
        source_dir_name: Name of the source directory (e.g., 'raw' or 'processed').
    """
    import yaml
    from datetime import datetime

    # Ensure state file exists
    if not state_file_path.exists():
        state_file_path.parent.mkdir(parents=True, exist_ok=True)
        state_file_path.touch()

    try:
        with open(state_file_path, 'r', encoding='utf-8') as f:
            state_data = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        logger.error(f"Error reading state file {state_file_path}: {e}")
        state_data = {}

    # Initialize structure if missing
    if 'data_checksums' not in state_data:
        state_data['data_checksums'] = {}

    if source_dir_name not in state_data['data_checksums']:
        state_data['data_checksums'][source_dir_name] = {
            'updated_at': datetime.utcnow().isoformat(),
            'files': {}
        }

    # Update files
    state_data['data_checksums'][source_dir_name]['files'].update(checksums)
    state_data['data_checksums'][source_dir_name]['updated_at'] = datetime.utcnow().isoformat()

    # Write back
    with open(state_file_path, 'w', encoding='utf-8') as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
    logger.info(f"Updated checksums for {source_dir_name} in {state_file_path}")