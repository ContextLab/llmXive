"""
loaders.py
----------
Helper utilities for loading large Parquet files.

The project works with potentially‑gigabyte‑scale datasets; loading the entire
file into memory may be impossible on the CI runner.  The two public helpers
are:

  * ``load_parquet_as_df(path)`` – convenience wrapper around ``pandas.read_parquet``
    that raises a clear ``FileNotFoundError`` if the file does not exist.

  * ``chunked_parquet_loader(path, batch_size=100_000)`` – generator that
    yields ``pandas.DataFrame`` objects of at most ``batch_size`` rows,
    using ``pyarrow.dataset`` for efficient streaming.
"""
from pathlib import Path
from typing import Generator

import pandas as pd
import pyarrow.dataset as ds

def load_parquet_as_df(path: Path) -> pd.DataFrame:
    """
    Load a Parquet file into a pandas DataFrame.

    Parameters
    ----------
    path: Path
        Path to the Parquet file.

    Returns
    -------
    pd.DataFrame

    Raises
    ------
    FileNotFoundError
        If ``path`` does not exist.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Parquet file not found: {path}")
    return pd.read_parquet(path)

def chunked_parquet_loader(path: Path, batch_size: int = 100_000) -> Generator[pd.DataFrame, None, None]:
    """
    Stream a Parquet file in chunks.

    Parameters
    ----------
    path: Path
        Path to the Parquet file.
    batch_size: int, optional
        Maximum number of rows per yielded DataFrame (default 100 000).

    Yields
    ------
    pd.DataFrame
        DataFrames containing up to ``batch_size`` rows.

    Notes
    -----
    The implementation uses ``pyarrow.dataset`` which can read columnar
    data without loading the whole file into memory.  Each batch is
    materialised as a pandas DataFrame for downstream compatibility.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Parquet file not found: {path}")

    dataset = ds.dataset(path, format="parquet")
    # ``to_table`` with ``batch_size`` returns an iterator of Arrow tables.
    for batch in dataset.to_batches(batch_size=batch_size):
        yield batch.to_pandas()
