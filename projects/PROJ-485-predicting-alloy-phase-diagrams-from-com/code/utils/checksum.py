"""
Checksum utilities for SHA-256 data verification.
Implements Constitution Principle III: Data Integrity via Cryptographic Hashing.
"""
import hashlib
import os
from typing import Optional, Tuple

from .logging import get_logger, log_error, log_info

logger = get_logger(__name__)

CHUNK_SIZE = 1024 * 1024  # 1 MB chunks for memory efficiency


def compute_file_sha256(file_path: str) -> Optional[str]:
    """
    Computes the SHA-256 hash of a file.

    Args:
        file_path: Absolute or relative path to the file.

    Returns:
        Hexadecimal string of the SHA-256 hash, or None if file not found or error.
    """
    if not os.path.exists(file_path):
        log_error(f"File not found for checksum: {file_path}", code="FILE_NOT_FOUND")
        return None

    sha256_hash = hashlib.sha256()

    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        log_error(f"Error computing checksum for {file_path}: {e}", code="CHECKSUM_ERROR")
        return None


def verify_file_checksum(file_path: str, expected_checksum: str) -> bool:
    """
    Verifies if a file's SHA-256 hash matches the expected checksum.

    Args:
        file_path: Path to the file.
        expected_checksum: The expected SHA-256 hex string.

    Returns:
        True if checksums match, False otherwise.
    """
    if not os.path.exists(file_path):
        log_error(f"Verification failed: File not found {file_path}", code="FILE_NOT_FOUND")
        return False

    computed = compute_file_sha256(file_path)

    if computed is None:
        return False

    if computed.lower() == expected_checksum.lower():
        log_info(f"Checksum verified for {file_path}: {computed}")
        return True
    else:
        log_error(
            f"Checksum mismatch for {file_path}. "
            f"Expected: {expected_checksum}, Got: {computed}",
            code="CHECKSUM_MISMATCH"
        )
        return False


def compute_and_store_checksum(file_path: str, output_path: Optional[str] = None) -> Tuple[bool, str]:
    """
    Computes checksum and optionally writes it to a file.
    Format: <hash>  <filename>

    Args:
        file_path: Path to the source file.
        output_path: Optional path to write the checksum file.

    Returns:
        Tuple of (success: bool, checksum: str)
    """
    checksum = compute_file_sha256(file_path)
    if checksum is None:
        return False, ""

    if output_path:
        try:
            with open(output_path, "w") as f:
                f.write(f"{checksum}  {os.path.basename(file_path)}\n")
            log_info(f"Checksum written to {output_path}")
        except Exception as e:
            log_error(f"Failed to write checksum to {output_path}: {e}", code="WRITE_ERROR")
            return False, checksum

    return True, checksum