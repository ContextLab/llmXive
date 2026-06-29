"""
utils/checksum.py
-----------------
Small helper utilities for reproducible data‑hashing and checksum verification.

The module provides functions to compute SHA‑256 hashes for raw bytes,
files on disk, and pandas DataFrames.  It also provides a simple verification
helper that compares an expected checksum with the actual file checksum.

The implementation purposefully avoids any randomness – the same input
always yields the same hash, which is essential for reproducible pipelines.
"""

import hashlib
from pathlib import Path
from typing import Union

import pandas as pd

__all__ = [
    "hash_bytes",
    "hash_file",
    "hash_dataframe",
    "verify_checksum",
]


def _ensure_path(path: Union[str, Path]) -> Path:
    """Coerce ``path`` to a :class:`~pathlib.Path` instance."""
    return path if isinstance(path, Path) else Path(path)


def hash_bytes(data: bytes) -> str:
    """
    Compute a SHA‑256 hash for a ``bytes`` object.

    Parameters
    ----------
    data: bytes
        Raw binary data to be hashed.

    Returns
    -------
    str
        Hexadecimal representation of the SHA‑256 digest.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("hash_bytes expects a bytes‑like object")
    return hashlib.sha256(data).hexdigest()


def hash_file(file_path: Union[str, Path]) -> str:
    """
    Compute a SHA‑256 hash for the contents of a file.

    The file is read in binary mode using a configurable chunk size
    (default 1 MiB) to avoid loading large files entirely into memory.

    Parameters
    ----------
    file_path: Union[str, Path]
        Path to the file whose checksum is required.

    Returns
    -------
    str
        Hexadecimal SHA‑256 digest of the file's contents.
    """
    path = _ensure_path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    sha256 = hashlib.sha256()
    chunk_size = 1024 * 1024  # 1 MiB

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def hash_dataframe(df: pd.DataFrame) -> str:
    """
    Compute a deterministic SHA‑256 hash for a :class:`pandas.DataFrame`.

    The function serialises the DataFrame to CSV **without** the index,
    using a fixed order of columns and a deterministic floating‑point
    representation.  This approach is simple, reproducible and does not
    depend on pandas' internal hash implementation (which can change
    across versions).

    Parameters
    ----------
    df: pandas.DataFrame
        DataFrame to be hashed.

    Returns
    -------
    str
        Hexadecimal SHA‑256 digest of the serialised DataFrame.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("hash_dataframe expects a pandas DataFrame")

    # Ensure a stable column order
    df_sorted = df.loc[:, sorted(df.columns)]

    # Serialize to CSV bytes; ``float_format`` guarantees deterministic
    # representation of floating point numbers.
    csv_bytes = df_sorted.to_csv(
        index=False,
        line_terminator="\n",
        float_format="%.12g",
    ).encode("utf-8")

    return hash_bytes(csv_bytes)


def verify_checksum(
    file_path: Union[str, Path],
    expected_checksum: str,
) -> bool:
    """
    Verify that the SHA‑256 checksum of ``file_path`` matches ``expected_checksum``.

    Parameters
    ----------
    file_path: Union[str, Path]
        Path to the file to be verified.
    expected_checksum: str
        Expected hexadecimal SHA‑256 digest.

    Returns
    -------
    bool
        ``True`` if the computed checksum matches the expected value,
        ``False`` otherwise.
    """
    actual = hash_file(file_path)
    return actual.lower() == expected_checksum.lower()
