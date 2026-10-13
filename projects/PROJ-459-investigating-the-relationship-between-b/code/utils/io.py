"""
I/O utilities for the project.

The original ``io`` module already provided ``ensure_dir`` and a few
helper functions.  For the current task we need ``save_parquet`` and
``load_parquet`` to be available because the placeholder pipeline steps
in ``code/main.py`` use them.  The implementations below rely on pandas’
built‑in parquet support (which is available via ``pyarrow`` in the
execution environment).
"""

import logging
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

def ensure_dir(path: Path) -> None:
    """Create ``path`` and any missing parents."""
    path.mkdir(parents=True, exist_ok=True)

def save_parquet(df: pd.DataFrame, file_path: Path) -> None:
    """
    Save a DataFrame to Parquet format.

    Parameters
    ----------
    df : pd.DataFrame
        Data to persist.
    file_path : Path
        Destination file (the parent directory is created if needed).
    """
    ensure_dir(file_path.parent)
    df.to_parquet(file_path, index=False)
    logger.info(f"Parquet saved to {file_path}")

def load_parquet(file_path: Path) -> pd.DataFrame:
    """
    Load a Parquet file into a DataFrame.

    Parameters
    ----------
    file_path : Path
        Path to the parquet file.

    Returns
    -------
    pd.DataFrame
    """
    if not file_path.is_file():
        raise FileNotFoundError(f"Parquet file not found: {file_path}")
    df = pd.read_parquet(file_path)
    logger.info(f"Parquet loaded from {file_path}")
    return df

def save_json(data: Any, file_path: Path) -> None:
    """Write ``data`` as JSON to ``file_path``."""
    ensure_dir(file_path.parent)
    import json

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info(f"JSON saved to {file_path}")

def load_json(file_path: Path) -> Any:
    """Read JSON from ``file_path``."""
    if not file_path.is_file():
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    import json

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    logger.info(f"JSON loaded from {file_path}")
    return data
