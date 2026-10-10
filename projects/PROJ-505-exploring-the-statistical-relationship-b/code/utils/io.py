"""
I/O utilities: checksumming and parquet loading/saving.
"""
import hashlib
from pathlib import Path
from typing import Optional

import pandas as pd

# ----------------------------------------------------------------------
# MD5 checksum helpers (retained for backward compatibility)
# ----------------------------------------------------------------------
def compute_md5(file_path: Path) -> str:
    """Compute MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def verify_md5(file_path: Path, expected_md5: str) -> bool:
    """Verify file checksum using MD5."""
    return compute_md5(file_path) == expected_md5

# ----------------------------------------------------------------------
# SHA-256 checksum helpers (required by the specification)
# ----------------------------------------------------------------------
def compute_sha256(file_path: Path) -> str:
    """Compute SHA‑256 checksum of a file."""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def verify_sha256(file_path: Path, expected_sha256: str) -> bool:
    """Verify file checksum using SHA‑256."""
    return compute_sha256(file_path) == expected_sha256

# ----------------------------------------------------------------------
# Parquet I/O helpers
# ----------------------------------------------------------------------
def load_parquet(file_path: Path) -> pd.DataFrame:
    """Load a parquet file into a DataFrame."""
    # pandas will select an appropriate engine (pyarrow, fastparquet, etc.).
    return pd.read_parquet(file_path)


def save_parquet(df: pd.DataFrame, file_path: Path) -> None:
    """Save a DataFrame to a parquet file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    # Use pandas' built‑in to_parquet; let pandas pick the engine.
    df.to_parquet(file_path, index=False)
