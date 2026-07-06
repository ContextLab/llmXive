"""
hasher.py - Generate SHA-256 hashes for artifacts (Constitution V).

This module provides utilities to compute and verify SHA-256 hashes
for files and strings, ensuring data integrity across the research pipeline.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Optional, Union

# Import shared logging utility
from .logging import get_logger

# Initialize logger
logger = get_logger(__name__)


def compute_file_hash(
    file_path: Union[str, Path],
    algorithm: str = "sha256",
    chunk_size: int = 8192
) -> str:
    """
    Compute the hash of a file using the specified algorithm.

    Args:
        file_path: Path to the file to hash.
        algorithm: Hash algorithm to use (default: 'sha256').
        chunk_size: Size of chunks to read at a time.

    Returns:
        Hexadecimal string of the hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        logger.error(f"File not found for hashing: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        hasher = hashlib.new(algorithm)
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest()
    except ValueError as e:
        logger.error(f"Unsupported hash algorithm '{algorithm}': {e}")
        raise
    except Exception as e:
        logger.error(f"Error computing hash for {file_path}: {e}")
        raise


def compute_string_hash(
    content: str,
    algorithm: str = "sha256",
    encoding: str = "utf-8"
) -> str:
    """
    Compute the hash of a string content.

    Args:
        content: String content to hash.
        algorithm: Hash algorithm to use (default: 'sha256').
        encoding: Encoding to use for string conversion (default: 'utf-8').

    Returns:
        Hexadecimal string of the hash.
    """
    try:
        hasher = hashlib.new(algorithm)
        hasher.update(content.encode(encoding))
        return hasher.hexdigest()
    except ValueError as e:
        logger.error(f"Unsupported hash algorithm '{algorithm}': {e}")
        raise
    except Exception as e:
        logger.error(f"Error computing hash for string: {e}")
        raise


def hash_artifact(
    artifact_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None
) -> str:
    """
    Hash an artifact and optionally save the hash to a .hash file.

    This implements the 'Constitution V' requirement for artifact integrity.

    Args:
        artifact_path: Path to the artifact file.
        output_path: Optional path to save the hash (default: artifact_path + '.hash').

    Returns:
        The computed hash string.
    """
    artifact_path = Path(artifact_path)
    if output_path is None:
        output_path = Path(str(artifact_path) + ".hash")
    else:
        output_path = Path(output_path)

    logger.info(f"Computing hash for artifact: {artifact_path}")
    file_hash = compute_file_hash(artifact_path)

    # Save hash to file
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(file_hash)
        logger.info(f"Hash saved to: {output_path}")
    except Exception as e:
        logger.warning(f"Failed to save hash to {output_path}: {e}")

    return file_hash


def verify_artifact_hash(
    artifact_path: Union[str, Path],
    hash_path: Optional[Union[str, Path]] = None
) -> bool:
    """
    Verify an artifact against its stored hash.

    Args:
        artifact_path: Path to the artifact file.
        hash_path: Path to the stored hash file (default: artifact_path + '.hash').

    Returns:
        True if the hash matches, False otherwise.
    """
    artifact_path = Path(artifact_path)
    if hash_path is None:
        hash_path = Path(str(artifact_path) + ".hash")
    else:
        hash_path = Path(hash_path)

    if not hash_path.exists():
        logger.warning(f"Hash file not found: {hash_path}")
        return False

    try:
        with open(hash_path, "r", encoding="utf-8") as f:
            stored_hash = f.read().strip()
    except Exception as e:
        logger.error(f"Failed to read hash file {hash_path}: {e}")
        return False

    computed_hash = compute_file_hash(artifact_path)

    if computed_hash == stored_hash:
        logger.info(f"Artifact integrity verified: {artifact_path}")
        return True
    else:
        logger.error(f"Artifact integrity check FAILED for {artifact_path}")
        logger.error(f"  Expected: {stored_hash}")
        logger.error(f"  Computed: {computed_hash}")
        return False


def hash_directory(
    directory_path: Union[str, Path],
    recursive: bool = True,
    extensions: Optional[list] = None
) -> str:
    """
    Compute a combined hash for all files in a directory.

    Args:
        directory_path: Path to the directory.
        recursive: Whether to include subdirectories.
        extensions: Optional list of file extensions to include (e.g., ['.py', '.txt']).

    Returns:
        A SHA-256 hash of the sorted concatenation of all file hashes.
    """
    directory_path = Path(directory_path)
    if not directory_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory_path}")

    logger.info(f"Hashing directory: {directory_path}")

    file_hashes = []

    if recursive:
        files = sorted(directory_path.rglob("*"))
    else:
        files = sorted(directory_path.glob("*"))

    for file_path in files:
        if file_path.is_file():
            if extensions:
                if file_path.suffix not in extensions:
                    continue
            try:
                h = compute_file_hash(file_path)
                file_hashes.append(f"{file_path.relative_to(directory_path)}:{h}")
            except Exception as e:
                logger.warning(f"Skipping file {file_path} due to error: {e}")

    if not file_hashes:
        logger.warning("No files found to hash in directory.")
        return compute_string_hash("")

    # Concatenate sorted hashes and hash the result
    combined = "\n".join(file_hashes)
    return compute_string_hash(combined)