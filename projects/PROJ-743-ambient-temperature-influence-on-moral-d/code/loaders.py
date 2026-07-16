"""
Data loading utilities for the Ambient Temperature Influence on Moral Decision Speed project.

Provides memory-efficient Parquet loading via chunked iteration to prevent
memory overflow when processing large datasets.
"""

import logging
import os
from pathlib import Path
from typing import Generator, Optional

import pandas as pd

from config import get_path_env_override

logger = logging.getLogger(__name__)


def load_chunked_parquet(
    path: str,
    chunk_size: int = 100000
) -> Generator[pd.DataFrame, None, None]:
    """
    Load a Parquet file in chunks to handle large datasets without memory overflow.

    This function uses pandas' `read_parquet` with the `chunksize` parameter
    (via the `pyarrow` engine) to return an iterator of DataFrames.

    Args:
        path: Path to the Parquet file. Can be relative to project root or absolute.
        chunk_size: Number of rows to read per chunk. Default is 100,000.

    Yields:
        pd.DataFrame: A chunk of the Parquet file as a DataFrame.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If chunk_size is not a positive integer.
        RuntimeError: If the file cannot be read as Parquet (e.g., wrong format).

    Note:
        This function relies on the `pyarrow` engine which is a dependency of pandas
        for Parquet support. Ensure `pyarrow` is installed if using the `chunksize`
        parameter in older pandas versions, though modern pandas handles this well.
    """
    if not isinstance(chunk_size, int) or chunk_size <= 0:
        raise ValueError(f"chunk_size must be a positive integer, got {chunk_size}")

    # Resolve path relative to project root if not absolute
    path_obj = Path(path)
    if not path_obj.is_absolute():
        project_root = get_path_env_override("PROJECT_ROOT", Path.cwd())
        path_obj = Path(project_root) / path_obj

    if not path_obj.exists():
        raise FileNotFoundError(f"Parquet file not found: {path_obj}")

    logger.info(f"Loading {path_obj} in chunks of {chunk_size} rows...")

    try:
        # read_parquet with chunksize returns a ParquetFile object which is iterable
        # or in newer pandas versions, an iterator directly depending on the engine.
        # We use the default engine (pyarrow) which supports chunking.
        parquet_file = pd.read_parquet(
            path_obj,
            engine="pyarrow",
            chunksize=chunk_size
        )

        for i, chunk in enumerate(parquet_file):
            logger.debug(f"Yielding chunk {i} with {len(chunk)} rows.")
            yield chunk

        logger.info(f"Successfully loaded {path_obj} in {i + 1} chunks.")

    except Exception as e:
        logger.error(f"Failed to read Parquet file {path_obj}: {e}")
        raise RuntimeError(f"Error reading Parquet file: {e}") from e


def load_parquet_as_df(path: str, chunk_size: int = 100000) -> pd.DataFrame:
    """
    Convenience function to load a Parquet file into a single DataFrame using chunked reading.

    This is useful when the dataset is large but fits in memory when fully concatenated,
    and you want to avoid loading it all at once during the read process.

    Args:
        path: Path to the Parquet file.
        chunk_size: Number of rows per chunk for the iterator.

    Returns:
        pd.DataFrame: The complete dataset concatenated from chunks.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If chunk_size is invalid.
        RuntimeError: If concatenation fails or file is unreadable.
    """
    chunks = []
    try:
        for chunk in load_chunked_parquet(path, chunk_size):
            chunks.append(chunk)

        if not chunks:
            logger.warning(f"No data found in {path}")
            return pd.DataFrame()

        logger.info(f"Concatenating {len(chunks)} chunks into a single DataFrame...")
        df = pd.concat(chunks, ignore_index=True)
        logger.info(f"Loaded {len(df)} total rows.")
        return df

    except Exception as e:
        logger.error(f"Failed to load and concatenate {path}: {e}")
        raise RuntimeError(f"Failed to load {path}: {e}") from e
