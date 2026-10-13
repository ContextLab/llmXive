"""
I/O helper utilities for the project.
Provides parquet read/write and SHA‑256 checksum functions.
"""
import hashlib
from pathlib import Path

import pandas as pd


def compute_sha256(file_path: Path) -> str:
    """Compute SHA‑256 checksum of a file."""
    hash_sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_sha.update(chunk)
    return hash_sha.hexdigest()


def verify_sha256(file_path: Path, expected_hash: str) -> bool:
    """Verify that the SHA‑256 checksum of a file matches the expected hash."""
    return compute_sha256(file_path) == expected_hash


def load_parquet(file_path: Path) -> pd.DataFrame:
    """Load a parquet file into a DataFrame."""
    return pd.read_parquet(file_path)


def save_parquet(df: pd.DataFrame, file_path: Path) -> None:
    """Save a DataFrame to parquet using pyarrow engine."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(file_path, index=False, engine="pyarrow")


__all__ = ["compute_sha256", "verify_sha256", "load_parquet", "save_parquet"]
