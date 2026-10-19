"""
Utility module for I/O operations with optional Parquet support.
Provides functions to save and load Parquet files with a fallback
to ``fastparquet`` when ``pyarrow`` is unavailable, as well as
SHA‑256 checksum utilities.
"""
import hashlib
from pathlib import Path
from typing import Any, Dict

import pandas as pd

# ----------------------------------------------------------------------
# Parquet I/O helpers
# ----------------------------------------------------------------------
def _get_parquet_engine() -> str:
    """
    Determine which Parquet engine is available.

    Returns:
        str: ``'pyarrow'`` if importable, otherwise ``'fastparquet'``.

    Raises:
        ImportError: If neither engine is available.
    """
    try:
        import pyarrow  # noqa: F401
        return "pyarrow"
    except Exception:
        try:
            import fastparquet  # noqa: F401
            return "fastparquet"
        except Exception as e:
            raise ImportError(
                "Neither 'pyarrow' nor 'fastparquet' is installed; "
                "install one to enable Parquet I/O."
            ) from e

def save_parquet(df: pd.DataFrame, path: str | Path) -> None:
    """
    Save a DataFrame to a Parquet file using the available engine.

    Args:
        df: DataFrame to write.
        path: Destination file path.
    """
    engine = _get_parquet_engine()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, engine=engine, index=False)

def load_parquet(path: str | Path) -> pd.DataFrame:
    """
    Load a Parquet file into a DataFrame using the available engine.

    Args:
        path: Path to the Parquet file.

    Returns:
        DataFrame read from the file.
    """
    engine = _get_parquet_engine()
    return pd.read_parquet(path, engine=engine)

# ----------------------------------------------------------------------
# Checksum helpers
# ----------------------------------------------------------------------
def sha256_checksum(file_path: str | Path) -> str:
    """
    Compute the SHA‑256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal SHA‑256 digest string.
    """
    file_path = Path(file_path)
    hash_sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

# Backwards‑compatible alias used by older code
compute_md5 = sha256_checksum
