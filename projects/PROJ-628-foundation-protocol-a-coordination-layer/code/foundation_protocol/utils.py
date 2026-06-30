"""
Foundation Protocol Utilities.

Provides deterministic seed logging and file hashing utilities
required for reproducibility and artifact verification (FR-008).
"""
import hashlib
import json
import os
import random
import time
from pathlib import Path
from typing import Optional


def log_seed(seed: int, output_dir: Optional[str] = None) -> str:
    """
    Logs a seed value to a deterministic JSON file to ensure reproducibility.

    Args:
        seed: The integer seed value to log.
        output_dir: Directory to write the log file. Defaults to 'data/seeds/'.
                    The file is named 'seed_log.json'.

    Returns:
        The absolute path to the created log file.

    Raises:
        ValueError: If the seed is not an integer.
        OSError: If the file cannot be written.
    """
    if not isinstance(seed, int):
        raise ValueError(f"Seed must be an integer, got {type(seed).__name__}")

    if output_dir is None:
        output_dir = "data/seeds"

    os.makedirs(output_dir, exist_ok=True)
    log_path = Path(output_dir) / "seed_log.json"

    record = {
        "seed": seed,
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "algorithm": "default",
    }

    # Write atomically by writing to a temp file first
    temp_path = log_path.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)

    os.replace(temp_path, log_path)

    return str(log_path.resolve())


def get_hash(file_path: str) -> str:
    """
    Computes the SHA-256 hash of a file's contents.

    This is used for verifying artifact integrity and reproducibility.

    Args:
        file_path: Path to the file to hash.

    Returns:
        The hexadecimal SHA-256 digest string.

    Raises:
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If the path points to a directory.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if os.path.isdir(file_path):
        raise IsADirectoryError(f"Path is a directory, not a file: {file_path}")

    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as f:
        # Read in chunks to handle large files without loading entirely into memory
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)

    return sha256_hash.hexdigest()
