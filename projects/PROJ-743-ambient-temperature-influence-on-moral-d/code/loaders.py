"""
loaders.py
----------
Simple helper for loading Parquet files in a memory‑efficient way.
The project frequently works with large datasets; this module provides
a thin wrapper around ``pandas.read_parquet`` that logs the operation
and can be swapped for a streaming implementation later without
touching downstream code.
"""
import logging
from pathlib import Path

import pandas as pd

from setup_logging import get_data_quality_logger


def load_parquet_as_df(parquet_path: str | Path) -> pd.DataFrame:
    """
    Load a Parquet file and return a DataFrame.

    Parameters
    ----------
    parquet_path: str or Path
        Path to the Parquet file.

    Returns
    -------
    pandas.DataFrame
        The loaded data.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    """
    logger: logging.Logger = get_data_quality_logger()
    path = Path(parquet_path)
    if not path.is_file():
        logger.error(f"Parquet file not found: {path}")
        raise FileNotFoundError(f"Parquet file not found: {path}")

    logger.info(f"Loading Parquet file: {path}")
    try:
        df = pd.read_parquet(path)
        logger.info(f"Loaded {len(df)} rows from {path}")
        return df
    except Exception as exc:
        logger.error(f"Failed to read Parquet file {path}: {exc}")
        raise
