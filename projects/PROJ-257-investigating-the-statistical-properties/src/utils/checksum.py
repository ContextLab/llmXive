"""
src.utils.checksum

Utility functions for computing and verifying SHA‑256 (or other) checksums
of files. These helpers are used by the GWTC download and data‑availability
scripts to ensure data integrity without any external dependencies.
"""

import hashlib
from pathlib import Path
from typing import Callable

__all__ = ["compute_file_hash", "verify_file"]


def _hash_file(path: Path, algo: Callable) -> str:
    """
    Compute a hash digest for ``path`` using the supplied ``hashlib`` algorithm
    constructor (e.g. ``hashlib.sha256``). The file is read in 8 MiB chunks
    to avoid loading large files entirely into memory.

    Parameters
    ----------
    path: Path
        Path to the file whose digest is to be computed.
    algo: Callable
        Callable that returns a new ``hashlib`` hash object (e.g.
        ``hashlib.sha256``).

    Returns
    -------
    str
        Hexadecimal digest string.
    """
    h = algo()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_file_hash(file_path: str, algorithm: str = "sha256") -> str:
    """
    Compute the cryptographic hash of ``file_path`` using the requested
    ``algorithm`` (default ``sha256``). Only algorithms supported by
    :mod:`hashlib` are allowed.

    Parameters
    ----------
    file_path: str
        Path to the target file.
    algorithm: str
        Name of the hash algorithm (e.g. ``'sha256'``).

    Returns
    -------
    str
        Hexadecimal digest.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found for hashing: {file_path}")

    try:
        algo_ctor = getattr(hashlib, algorithm.lower())
    except AttributeError as exc:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}") from exc

    return _hash_file(path, algo_ctor)


def verify_file(file_path: str, expected_hash: str, algorithm: str = "sha256") -> bool:
    """
    Verify that ``file_path`` exists and its hash matches ``expected_hash``.

    Parameters
    ----------
    file_path: str
        Path to the file to verify.
    expected_hash: str
        Expected hexadecimal digest.
    algorithm: str
        Hash algorithm used to compute ``expected_hash`` (default ``sha256``).

    Returns
    -------
    bool
        ``True`` if the file exists and the computed hash equals
        ``expected_hash``; ``False`` otherwise.
    """
    try:
        actual = compute_file_hash(file_path, algorithm=algorithm)
    except Exception:
        return False
    return actual.lower() == expected_hash.lower()
