"""
Streaming utilities for ingestion modules.

Provides helpers to stream large CSV or JSON resources from URLs without
loading the entire content into memory at once. The functions return
iterators (pandas DataFrames for CSV) that can be processed chunk‑by‑chunk.

These utilities are deliberately lightweight and rely only on the
standard library and pandas, which is already a project dependency.
"""

import logging
from typing import Iterator, Optional

import pandas as pd
import requests

logger = logging.getLogger(__name__)


def stream_csv(url: str, chunksize: int = 1000, **read_csv_kwargs) -> Iterator[pd.DataFrame]:
    """
    Stream a remote CSV file from ``url`` using pandas' chunked reader.

    Parameters
    ----------
    url: str
        The HTTP(S) URL pointing to a CSV file.
    chunksize: int, default 1000
        Number of rows per chunk returned by the iterator.
    **read_csv_kwargs:
        Additional keyword arguments passed to ``pd.read_csv``.

    Yields
    ------
    pandas.DataFrame
        DataFrame containing up to ``chunksize`` rows.

    Notes
    -----
    The function uses ``requests`` with ``stream=True`` to avoid downloading
    the whole file into memory. pandas can read directly from the URL, but
    setting ``stream=True`` ensures the HTTP connection is not eagerly
    consumed before pandas begins iterating.
    """
    logger.info(f"Streaming CSV from {url} with chunksize={chunksize}")
    try:
        # ``requests`` will handle streaming; pandas can read from the URL.
        # Passing the URL directly to ``pd.read_csv`` with ``chunksize`` triggers
        # pandas to open the connection lazily.
        for chunk in pd.read_csv(url, chunksize=chunksize, **read_csv_kwargs):
            yield chunk
    except Exception as exc:
        logger.error(f"Failed to stream CSV from {url}: {exc}")
        raise
        

def stream_json(
    url: str,
    params: Optional[dict] = None,
    headers: Optional[dict] = None,
    timeout: int = 30,
) -> Iterator[dict]:
    """
    Stream a JSON response from ``url``.

    This helper assumes the endpoint returns a JSON object with a top‑level
    ``data`` list (as used by the Materials Project API). It yields each
    element of that list individually, allowing callers to process records
    without holding the entire payload in memory.

    Parameters
    ----------
    url: str
        The endpoint returning JSON.
    params: dict, optional
        Query parameters passed to ``requests.get``.
    headers: dict, optional
        HTTP headers (e.g., API keys).
    timeout: int, default 30
        Seconds to wait for the server response.

    Yields
    ------
    dict
        Individual record dictionaries from the JSON payload.

    Raises
    ------
    requests.RequestException
        If the HTTP request fails.
    ValueError
        If the response cannot be parsed as JSON or does not contain a
        ``data`` field.
    """
    logger.info(f"Streaming JSON from {url}")
    try:
        response = requests.get(url, params=params, headers=headers, timeout=timeout, stream=True)
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        logger.error(f"Failed to fetch JSON from {url}: {exc}")
        raise

    if not isinstance(payload, dict) or "data" not in payload:
        raise ValueError("JSON payload does not contain expected 'data' field")

    for item in payload["data"]:
        yield item
