"""
Chunked Parquet Loader Utilities

This module provides helper functions for loading large Parquet files in a
memory‑efficient way using pyarrow's dataset API. It is used throughout the
pipeline (e.g., in ingestion, modeling, robustness) to avoid loading the
entire file into memory when it is unnecessary.

Functions
----------
load_parquet_as_df(path: str | Path, columns: list | None = None) -> pandas.DataFrame
    Load the whole Parquet file as a DataFrame (convenient wrapper).

iter_parquet_chunks(path: str | Path, batch_size: int = 100_000, columns: list | None = None)
    Generator yielding DataFrames of size ``batch_size`` rows. Useful for
    streaming large datasets without exhausting RAM.
"""
import os
from pathlib import Path
from typing import Generator, List, Optional, Union

import pandas as pd
import pyarrow.dataset as ds

def _ensure_path(path: Union[str, Path]) -> Path:
    """Validate that the given path exists and is a file."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Parquet file not found: {p}")
    return p

def load_parquet_as_df(
    path: Union[str, Path],
    columns: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Load a Parquet file into a pandas DataFrame.

    Parameters
    ----------
    path : str or Path
        Path to the Parquet file.
    columns : list of str, optional
        Subset of columns to read. If None, all columns are read.

    Returns
    -------
    pandas.DataFrame
        The loaded data.
    """
    p = _ensure_path(path)
    # Using pyarrow.dataset for efficient column projection
    table = ds.dataset(p, format="parquet").to_table(columns=columns)
    return table.to_pandas()

def iter_parquet_chunks(
    path: Union[str, Path],
    batch_size: int = 100_000,
    columns: Optional[List[str]] = None,
) -> Generator[pd.DataFrame, None, None]:
    """
    Iterate over a Parquet file in chunks.

    Parameters
    ----------
    path : str or Path
        Path to the Parquet file.
    batch_size : int, default 100_000
        Number of rows per yielded chunk.
    columns : list of str, optional
        Columns to read; None reads all.

    Yields
    ------
    pandas.DataFrame
        Chunk of rows from the Parquet file.
    """
    p = _ensure_path(path)
    dataset = ds.dataset(p, format="parquet")
    # Scan with optional column projection
    scanner = dataset.scan(columns=columns)

    # Use the pyarrow RecordBatch iterator and convert each batch to pandas
    for batch in scanner.to_batches():
        df = batch.to_pandas()
        # If the batch is larger than the desired size, split it further
        if len(df) <= batch_size:
            yield df
        else:
            # Split large batch into smaller pieces
            for start in range(0, len(df), batch_size):
                yield df.iloc[start:start + batch_size]
