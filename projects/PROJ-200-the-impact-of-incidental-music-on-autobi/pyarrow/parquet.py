"""
Stub implementation of ``pyarrow.parquet``.

Only the functions that the project calls are provided:

* ``write_table(table, where, **kwargs)`` – ``table`` is a ``pandas.DataFrame``.
  The function forwards to ``DataFrame.to_parquet``.
* ``read_table(source, **kwargs)`` – reads a Parquet file and returns a
  ``pandas.DataFrame``.
"""
from __future__ import annotations

import pandas as pd
from pathlib import Path
from typing import Any

def write_table(table: pd.DataFrame, where: str | Path, **kwargs: Any) -> None:
    """
    Write a ``pandas.DataFrame`` to a Parquet file.

    Parameters
    ----------
    table: pd.DataFrame
        Data to be persisted.
    where: str or Path
        Destination file path.
    **kwargs:
        Additional arguments accepted by ``DataFrame.to_parquet``.
    """
    path = Path(where)
    path.parent.mkdir(parents=True, exist_ok=True)
    table.to_parquet(path, index=False, **kwargs)


def read_table(source: str | Path, **kwargs: Any) -> pd.DataFrame:
    """
    Read a Parquet file into a ``pandas.DataFrame``.

    Parameters
    ----------
    source: str or Path
        Path to the Parquet file.
    **kwargs:
        Additional arguments accepted by ``pd.read_parquet``.
    """
    path = Path(source)
    return pd.read_parquet(path, **kwargs)
