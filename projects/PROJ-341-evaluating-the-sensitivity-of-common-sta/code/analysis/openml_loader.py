"""
Helper utilities for loading OpenML datasets in a memory‑conservative way.
Currently provides a chunked loader for the Adult dataset (OpenML ID 1590).
"""
from __future__ import annotations

import pandas as pd
from typing import Iterable

# The tolerant logger used throughout the project
from code.simulation.logging_config import get_logger

logger = get_logger(__name__)


def _read_csv_in_chunks(url: str, *, chunksize: int = 10_000, max_rows: int = 5_000) -> pd.DataFrame:
    """
    Stream a remote CSV via pandas and accumulate up to ``max_rows`` rows.

    Parameters
    ----------
    url: str
        Direct URL to the CSV file.
    chunksize: int, default 10 000
        Number of rows to request per iteration.
    max_rows: int, default 5 000
        Upper bound on the total rows to materialise in memory.

    Returns
    -------
    pd.DataFrame
        Concatenated DataFrame containing at most ``max_rows`` rows.
    """
    logger.log(
        "openml_chunked_load_start",
        url=url,
        chunksize=chunksize,
        max_rows=max_rows,
    )

    chunks: list[pd.DataFrame] = []
    total = 0

    for chunk in pd.read_csv(url, chunksize=chunksize, low_memory=False):
        chunks.append(chunk)
        total += len(chunk)
        if total >= max_rows:
            break

    df = pd.concat(chunks, ignore_index=True)
    if len(df) > max_rows:
        df = df.head(max_rows)

    logger.log("openml_chunked_load_complete", rows=len(df))
    return df


def load_adult_dataset_chunked(
    *,
    max_rows: int = 5_000,
    chunksize: int = 10_000,
) -> pd.DataFrame:
    """
    Load the UCI Adult dataset from OpenML (ID 1590) without pulling the
    entire file into RAM. The function streams the CSV source and returns
    at most ``max_rows`` rows (default 5 000), which is sufficient for the
    downstream validation steps while keeping memory usage well below the
    7 GB limit.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing a (potentially sampled) slice of the Adult data.
    """
    import openml

    dataset_id = 1590
    logger.log("adult_dataset_load_requested", dataset_id=dataset_id, max_rows=max_rows)

    # Retrieve the dataset metadata; this does **not** download the data.
    ds = openml.datasets.get_dataset(dataset_id, download_all_files=False)

    # The data file URL points to a CSV representation of the ARFF source.
    data_url = ds.get_data_file_url()
    logger.log("adult_dataset_url_obtained", url=data_url)

    df = _read_csv_in_chunks(data_url, chunksize=chunksize, max_rows=max_rows)

    # OpenML's Adult file includes a trailing '?' for missing values; pandas reads them as strings.
    # Convert common missing markers to NaN for downstream compatibility.
    df.replace("?", pd.NA, inplace=True)

    logger.log("adult_dataset_loaded", rows=len(df))
    return df
