"""
src.utils.checksum

Utility functions for computing and verifying file checksums.
Used by the GWTC download and data‑availability scripts to ensure
integrity of the downloaded HDF5 archives.
"""

import hashlib
from pathlib import Path
from typing import Union

def compute_file_hash(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Compute the cryptographic hash of a file.

    Parameters
    ----------
    file_path : str or pathlib.Path
        Path to the file whose hash should be computed.
    algorithm : str, optional
        Hash algorithm to use (default ``\"sha256\"``). Must be supported by
        :mod:`hashlib`.

    Returns
    -------
    str
        Hex‑digest of the file content.

    Raises
    ------
    FileNotFoundError
        If the supplied path does not exist.
    ValueError
        If the requested algorithm is not available in ``hashlib``.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found for hashing: {path}")

    try:
        hasher = hashlib.new(algorithm)
    except ValueError as exc:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}") from exc

    # Read the file in binary mode in chunks to avoid excessive memory use.
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def verify_file(file_path: Union[str, Path], expected_hash: str, algorithm: str = "sha256") -> bool:
    """
    Verify that a file's hash matches an expected value.

    Parameters
    ----------
    file_path : str or pathlib.Path
        Path to the file to verify.
    expected_hash : str
        Expected hex‑digest of the file.
    algorithm : str, optional
        Hash algorithm used for the expected digest (default ``\"sha256\"``).

    Returns
    -------
    bool
        ``True`` if the computed hash equals ``expected_hash``, otherwise ``False``.
    """
    try:
        computed = compute_file_hash(file_path, algorithm=algorithm)
        return computed.lower() == expected_hash.lower()
    except Exception:
        # Any error (missing file, unsupported algorithm, etc.) is treated as a verification failure.
        return False
