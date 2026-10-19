"""
I/O helper utilities for the project.
Provides parquet read/write and SHA-256 checksum functions.

Parquet I/O does NOT hard-require ``pyarrow``: the module attempts to
import ``pyarrow`` first, falls back to ``fastparquet``, and raises a
clear error only if both engines are missing.
"""
import hashlib
from pathlib import Path

import pandas as pd

try:  # preferred engine
    import pyarrow  # noqa: F401
    _PARQUET_ENGINE = "pyarrow"
except ImportError:
    try:
        import fastparquet  # noqa: F401
        _PARQUET_ENGINE = "fastparquet"
    except ImportError:
        _PARQUET_ENGINE = None


def get_parquet_engine() -> str:
    """Return the available parquet engine name ('pyarrow' or 'fastparquet')."""
    if _PARQUET_ENGINE is None:
        raise ImportError(
            "No parquet engine available. Install either 'pyarrow' or "
            "'fastparquet' to enable parquet I/O."
        )
    return _PARQUET_ENGINE


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    hash_sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_sha.update(chunk)
    return hash_sha.hexdigest()


# Alias required by the task specification.
sha256_checksum = compute_sha256


def verify_sha256(file_path: Path, expected_hash: str) -> bool:
    """Verify that the SHA-256 checksum of a file matches the expected hash."""
    return compute_sha256(file_path) == expected_hash


def load_parquet(file_path: Path) -> pd.DataFrame:
    """Load a parquet file into a DataFrame."""
    return pd.read_parquet(file_path, engine=get_parquet_engine())


def save_parquet(df: pd.DataFrame, file_path: Path) -> None:
    """Save a DataFrame to parquet using pyarrow, falling back to fastparquet."""
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(file_path, index=False, engine=get_parquet_engine())


__all__ = [
    "compute_sha256",
    "sha256_checksum",
    "verify_sha256",
    "load_parquet",
    "save_parquet",
    "get_parquet_engine",
]
