"""
I/O helper utilities for the project.

Provides robust CSV/Parquet read/write functions that gracefully
handle the optional presence of either ``pyarrow`` or ``fastparquet``
without hard dependencies on either. Also includes SHA‑256 checksum
generation for data‑integrity verification.
"""
import hashlib
import logging
from pathlib import Path
from typing import Any

import pandas as pd

# Optional imports – handled lazily in the helper functions
try:
    import pyarrow  # noqa: F401
    _HAS_PYARROW = True
except Exception:  # pragma: no cover
    _HAS_PYARROW = False

try:
    import fastparquet  # noqa: F401
    _HAS_FASTPARQUET = True
except Exception:  # pragma: no cover
    _HAS_FASTPARQUET = False

logger = logging.getLogger(__name__)

def _choose_parquet_engine() -> str:
    """
    Choose a parquet engine based on availability.

    Preference order:
    1. pyarrow (if installed)
    2. fastparquet (if installed)
    Raises RuntimeError if neither is available.
    """
    if _HAS_PYARROW:
        return "pyarrow"
    if _HAS_FASTPARQUET:
        return "fastparquet"
    raise RuntimeError(
        "Neither 'pyarrow' nor 'fastparquet' is available for Parquet I/O. "
        "Install one of them or adjust requirements."
    )

def save_parquet(df: pd.DataFrame, path: Path | str) -> None:
    """
    Save a DataFrame to a Parquet file using the available engine.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to be saved.
    path : Path | str
        Destination file path.
    """
    engine = _choose_parquet_engine()
    logger.debug("Saving Parquet with engine='%s' to %s", engine, path)
    df.to_parquet(path, engine=engine, index=False)

def load_parquet(path: Path | str) -> pd.DataFrame:
    """
    Load a Parquet file into a DataFrame using the available engine.

    Parameters
    ----------
    path : Path | str
        Path to the Parquet file.

    Returns
    -------
    pd.DataFrame
        Loaded DataFrame.
    """
    engine = _choose_parquet_engine()
    logger.debug("Loading Parquet with engine='%s' from %s", engine, path)
    return pd.read_parquet(path, engine=engine)

def sha256_checksum(file_path: Path | str) -> str:
    """
    Compute the SHA‑256 checksum of a file.

    Parameters
    ----------
    file_path : Path | str
        Path to the file.

    Returns
    -------
    str
        Hexadecimal SHA‑256 digest.
    """
    file_path = Path(file_path)
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            sha256.update(chunk)
    return sha256.hexdigest()