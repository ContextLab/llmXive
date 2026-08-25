"""
Data integrity utilities for the llmXive phylogeny-metabolite pipeline.

Provides:
  - Checksum verification (SHA-256)
  - Streaming file iterators for large files (memory-safe)
  - Error handling wrappers with logging integration
"""

import hashlib
import os
from pathlib import Path
from typing import Iterator, BinaryIO, Callable, Any, Optional, TextIO
import logging

from config import calculate_checksum as config_checksum, validate_file_integrity as config_validate
from entities import PlantSpecies, PhylogeneticTree, MetaboliteProfile, DistanceMatrix

logger = logging.getLogger(__name__)


def verify_checksum(file_path: str | Path, expected_hash: str, algorithm: str = "sha256") -> bool:
    """
    Verify the SHA-256 (or other) checksum of a file against an expected value.

    Args:
        file_path: Path to the file to verify.
        expected_hash: The expected hex digest string.
        algorithm: Hash algorithm to use (default 'sha256').

    Returns:
        True if the computed hash matches the expected hash, False otherwise.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is unsupported.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        logger.error(f"File not found for checksum verification: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        computed_hash = calculate_checksum(str(file_path), algorithm)
    except Exception as e:
        logger.error(f"Failed to compute checksum for {file_path}: {e}")
        raise

    if computed_hash.lower() == expected_hash.lower():
        logger.info(f"Checksum verified for {file_path} ({algorithm}): {computed_hash[:16]}...")
        return True
    else:
        logger.error(
            f"Checksum mismatch for {file_path}. Expected: {expected_hash}, Got: {computed_hash}"
        )
        return False


def stream_file_lines(
    file_path: str | Path,
    chunk_size: int = 8192,
    encoding: str = "utf-8"
) -> Iterator[str]:
    """
    Stream a file line-by-line to avoid loading large files into memory.

    Args:
        file_path: Path to the file.
        chunk_size: Number of bytes to read at a time.
        encoding: Text encoding to use.

    Yields:
        Lines from the file as strings.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    buffer = ""
    with open(file_path, "r", encoding=encoding) as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                if buffer:
                    yield buffer
                break
            buffer += chunk
            lines = buffer.split("\n")
            buffer = lines[-1]
            for line in lines[:-1]:
                yield line


def stream_binary_file(
    file_path: str | Path,
    chunk_size: int = 65536
) -> Iterator[bytes]:
    """
    Stream a binary file in chunks.

    Args:
        file_path: Path to the binary file.
        chunk_size: Number of bytes to read per iteration.

    Yields:
        Chunks of bytes from the file.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk


def safe_file_operation(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to wrap file operations with robust error handling and logging.

    Catches common file I/O errors and logs them with context before re-raising
    as a generic RuntimeError with the original exception attached, or returns
    a specific failure signal if configured.

    Args:
        func: The file operation function to wrap.

    Returns:
        The wrapped function.
    """
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            logger.error(f"File not found during operation {func.__name__}: {e}")
            raise
        except PermissionError as e:
            logger.error(f"Permission denied during operation {func.__name__}: {e}")
            raise
        except IsADirectoryError as e:
            logger.error(f"Expected file but got directory during operation {func.__name__}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during operation {func.__name__}: {e}")
            raise RuntimeError(f"Operation {func.__name__} failed unexpectedly") from e
    return wrapper


@safe_file_operation
def read_fasta_header(file_path: str | Path) -> Optional[str]:
    """
    Safely read the first header line from a FASTA file.

    Args:
        file_path: Path to the FASTA file.

    Returns:
        The header string (without '>') or None if empty.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"FASTA file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        first_line = f.readline().strip()
        if first_line.startswith(">"):
            return first_line[1:]
        return None


def validate_data_integrity(
    data: PlantSpecies | PhylogeneticTree | MetaboliteProfile | DistanceMatrix | dict,
    rules: dict
) -> tuple[bool, list[str]]:
    """
    Validate data objects against a set of integrity rules.

    Args:
        data: The data object to validate.
        rules: A dictionary of rule names to check functions.
               e.g., {"has_species": lambda d: hasattr(d, 'species') and len(d.species) > 0}

    Returns:
        A tuple (is_valid, list_of_error_messages).
    """
    errors = []
    for rule_name, check_func in rules.items():
        try:
            if not check_func(data):
                errors.append(f"Rule failed: {rule_name}")
        except Exception as e:
            errors.append(f"Rule error ({rule_name}): {e}")

    is_valid = len(errors) == 0
    if not is_valid:
        logger.warning(f"Data integrity validation failed with {len(errors)} errors")
    else:
        logger.info("Data integrity validation passed")
    return is_valid, errors