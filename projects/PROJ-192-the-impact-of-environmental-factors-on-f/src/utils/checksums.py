"""
Checksum verification utilities for data integrity.

Provides functions to compute and verify SHA256 checksums for files
downloaded or processed in the research pipeline.
"""

import hashlib
import os
from pathlib import Path
from typing import Optional, Tuple


def compute_sha256(file_path: Union[str, Path], chunk_size: int = 8192) -> str:
    """
    Compute the SHA256 hash of a file.

    Reads the file in chunks to handle large files (e.g., FASTQs) without
    loading them entirely into memory.

    Args:
        file_path: Path to the file to hash.
        chunk_size: Size of chunks to read at a time.

    Returns:
        The hexadecimal SHA256 hash string.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If there is an error reading the file.
    """
    sha256_hash = hashlib.sha256()
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)

    return sha256_hash.hexdigest()


def verify_checksum(
    file_path: Union[str, Path],
    expected_checksum: str,
    algorithm: str = "sha256",
) -> Tuple[bool, str]:
    """
    Verify a file's checksum against an expected value.

    Args:
        file_path: Path to the file to verify.
        expected_checksum: The expected hex digest string.
        algorithm: The hashing algorithm to use (currently only 'sha256' supported).

    Returns:
        A tuple (is_valid, message) where is_valid is True if the checksum matches.
    """
    if algorithm.lower() != "sha256":
        raise ValueError(f"Unsupported algorithm: {algorithm}. Only 'sha256' is supported.")

    try:
        actual_checksum = compute_sha256(file_path)
        is_valid = actual_checksum.lower() == expected_checksum.lower()
        message = (
            "Checksum verification successful."
            if is_valid
            else f"Checksum mismatch. Expected: {expected_checksum}, Got: {actual_checksum}"
        )
        return is_valid, message
    except FileNotFoundError as e:
        return False, f"File not found during verification: {e}"
    except Exception as e:
        return False, f"Verification error: {e}"


def generate_checksum_file(file_path: Union[str, Path], output_dir: Optional[Union[str, Path]] = None) -> Path:
    """
    Generate a .sha256 file containing the checksum for a given file.

    Args:
        file_path: The file to checksum.
        output_dir: Directory to write the checksum file. Defaults to the file's directory.

    Returns:
        Path to the generated checksum file.
    """
    file_path = Path(file_path)
    if output_dir is None:
        output_dir = file_path.parent
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    checksum_value = compute_sha256(file_path)
    checksum_filename = f"{file_path.name}.sha256"
    checksum_path = output_dir / checksum_filename

    # Format: <hash>  <filename> (two spaces as per standard sha256sum output)
    with open(checksum_path, "w") as f:
        f.write(f"{checksum_value}  {file_path.name}\n")

    return checksum_path
