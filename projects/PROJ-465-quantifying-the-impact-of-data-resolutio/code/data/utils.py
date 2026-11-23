"""
Utility functions for data handling and integrity verification.

This module provides functions for verifying checksums of raw data files
and generating checksum manifests for data provenance.
"""
import hashlib
import os
import logging
from pathlib import Path
from typing import Union, Optional

from code.utils.hash_artifact import compute_file_hash
from code.config import DATA_RAW_DIR


logger = logging.getLogger(__name__)


def verify_checksum(file_path: Union[str, Path], expected_checksum: str) -> bool:
    """
    Verify the checksum of a file against an expected value.

    Args:
        file_path: Path to the file to verify.
        expected_checksum: The expected SHA-256 checksum.

    Returns:
        True if the file's checksum matches the expected value, False otherwise.
    """
    path = Path(file_path)
    if not path.exists():
        logger.error(f"File not found for checksum verification: {path}")
        return False

    computed_checksum = compute_file_hash(path)
    if computed_checksum == expected_checksum:
        logger.info(f"Checksum verified for {path.name}")
        return True
    else:
        logger.error(
            f"Checksum mismatch for {path.name}. "
            f"Expected: {expected_checksum}, Computed: {computed_checksum}"
        )
        return False


def generate_checksum_file(
    file_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None
) -> str:
    """
    Generate a checksum file for a given data file.

    Args:
        file_path: Path to the file to checksum.
        output_path: Optional path for the checksum file. If None, a file
                     named '<filename>.sha256' will be created in the same
                     directory as the source file.

    Returns:
        The path to the generated checksum file.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if output_path is None:
        output_path = path.with_suffix(path.suffix + ".sha256")
    else:
        output_path = Path(output_path)

    checksum = compute_file_hash(path)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"{checksum}  {path.name}\n")

    logger.info(f"Checksum file generated: {output_path}")
    return str(output_path)
