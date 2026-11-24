"""
Corruption Handler
------------------
Provides a simple SHA‑256 integrity check for files downloaded from
OpenNeuro. The function raises on mismatch – adhering to the *fail‑loudly*
policy.
"""

import hashlib
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA‑256 hash of ``file_path`` in a streaming fashion.

    Parameters
    ----------
    file_path : Path

    Returns
    -------
    str
        Hexadecimal SHA‑256 digest.
    """
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_file_integrity(file_path: Path, expected_hash: str) -> None:
    """
    Verify that ``file_path`` matches ``expected_hash``. Raises
    ``ValueError`` on mismatch.

    Parameters
    ----------
    file_path : Path
    expected_hash : str
    """
    actual_hash = compute_sha256(file_path)
    if actual_hash.lower() != expected_hash.lower():
        raise ValueError(
            f"Integrity check failed for {file_path}. "
            f"Expected {expected_hash}, got {actual_hash}."
        )
    logger.info(f"Integrity verified for {file_path}")
