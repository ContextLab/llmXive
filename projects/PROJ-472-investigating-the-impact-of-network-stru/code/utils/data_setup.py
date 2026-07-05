import os
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional
from config import get_data_root
from utils.logger import get_logger

logger = get_logger(__name__)

def compute_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
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

    hash_func = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def load_checksums(checksum_file: Path) -> Dict[str, str]:
    """
    Load existing checksums from a JSON manifest file.

    Args:
        checksum_file: Path to the JSON manifest file.

    Returns:
        Dictionary mapping relative file paths to their checksums.
    """
    if not checksum_file.exists():
        return {}

    with open(checksum_file, 'r') as f:
        return json.load(f)

def save_checksums(checksums: Dict[str, str], checksum_file: Path) -> None:
    """
    Save checksums to a JSON manifest file.

    Args:
        checksums: Dictionary mapping relative file paths to checksums.
        checksum_file: Path to the JSON manifest file.
    """
    checksum_file.parent.mkdir(parents=True, exist_ok=True)
    with open(checksum_file, 'w') as f:
        json.dump(checksums, f, indent=2)

def update_checksum_for_file(file_path: Path, checksums: Dict[str, str], checksum_file: Path) -> None:
    """
    Update the checksum for a specific file in the manifest.

    Args:
        file_path: Absolute path to the file.
        checksums: Current dictionary of checksums (updated in-place).
        checksum_file: Path to the JSON manifest file.
    """
    if not file_path.exists():
        logger.warning(f"Cannot update checksum: file not found {file_path}")
        return

    rel_path = str(file_path.relative_to(get_data_root()))
    checksums[rel_path] = compute_file_checksum(file_path)
    save_checksums(checksums, checksum_file)
    logger.info(f"Updated checksum for {rel_path}")

def verify_file_integrity(file_path: Path, checksums: Dict[str, str], checksum_file: Path) -> bool:
    """
    Verify the integrity of a file against its stored checksum.

    Args:
        file_path: Absolute path to the file.
        checksums: Dictionary of stored checksums.
        checksum_file: Path to the JSON manifest file (used if checksums is empty).

    Returns:
        True if the file is valid, False otherwise.
    """
    if not file_path.exists():
        logger.error(f"Verification failed: file not found {file_path}")
        return False

    if not checksums:
        checksums = load_checksums(checksum_file)

    rel_path = str(file_path.relative_to(get_data_root()))
    stored_checksum = checksums.get(rel_path)

    if not stored_checksum:
        logger.warning(f"No checksum found for {rel_path}. Skipping verification.")
        return False

    current_checksum = compute_file_checksum(file_path)
    if current_checksum != stored_checksum:
        logger.error(f"Checksum mismatch for {rel_path}. Expected: {stored_checksum}, Got: {current_checksum}")
        return False

    logger.info(f"Checksum verified for {rel_path}")
    return True

def setup_data_environment() -> Dict[Path, Path]:
    """
    Create the required data directory structure and initialize the checksum manifest.

    Creates:
        - data/raw
        - data/processed
        - data/results

    Initializes:
        - data/.checksums.json

    Returns:
        Dictionary mapping directory names to their absolute Path objects.
    """
    data_root = get_data_root()
    data_root.mkdir(parents=True, exist_ok=True)

    directories = ['raw', 'processed', 'results']
    paths = {}

    for dir_name in directories:
        dir_path = data_root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        paths[dir_name] = dir_path
        logger.info(f"Created directory: {dir_path}")

    checksum_file = data_root / '.checksums.json'
    if not checksum_file.exists():
        save_checksums({}, checksum_file)
        logger.info(f"Initialized checksum manifest: {checksum_file}")
    else:
        logger.info(f"Checksum manifest already exists: {checksum_file}")

    return paths

if __name__ == "__main__":
    setup_data_environment()
    logger.info("Data environment setup complete.")
