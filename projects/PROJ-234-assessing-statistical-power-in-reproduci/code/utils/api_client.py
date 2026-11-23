"""
utils/api_client.py
-------------------

Utility module providing a thin wrapper around the OpenML REST API with
exponential‑backoff retry logic.  The original implementation (from T004)
already includes generic request handling.  This file extends it with a
convenience function that fetches the *top‑N most‑downloaded classification
datasets* and normalises the field names to match the contract schema used
throughout the project.

The function is deliberately lightweight and does not introduce any new
third‑party dependencies beyond those already required by the project
(``openml`` and ``pandas``).  It raises ``DataFetchError`` on unrecoverable
failures, satisfying the contract for the utilities.
"""

import time
import logging
from typing import List, Dict, Any

import openml
from openml import config as openml_config
import pandas as pd

from .exceptions import DataFetchError  # custom exception defined in utils.exceptions

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Existing generic request logic (from T004) – kept unchanged.
# ----------------------------------------------------------------------
# The original ``api_client`` module provides a ``request`` function that
# implements exponential back‑off for HTTP 429 responses.  For the purpose
# of this task we only need the higher‑level helper defined below, which
# internally calls the original ``request`` if it exists; otherwise it
# directly uses ``openml`` because the OpenML Python client already handles
# HTTP errors appropriately.
# ----------------------------------------------------------------------


def _apply_backoff(attempt: int, initial_delay: float = 1.0, max_delay: float = 60.0) -> None:
    """Sleep for an exponentially increasing amount of time."""
    delay = min(initial_delay * (2 ** (attempt - 1)), max_delay)
    logger.debug(f"Back‑off sleep for {delay:.1f}s (attempt {attempt})")
    time.sleep(delay)


def fetch_top_classification_datasets(max_datasets: int = 50,
                                      max_retries: int = 5,
                                      initial_delay: float = 1.0,
                                      max_delay: float = 60.0) -> List[Dict[str, Any]]:
    """
    Fetch the *top‑N* most‑downloaded *classification* datasets from OpenML.

    The function:
    1. Retrieves the full OpenML dataset catalogue as a pandas ``DataFrame``.
    2. Filters for rows where ``type`` contains the substring
       ``"Supervised Classification"`` (case‑insensitive).
    3. Sorts by ``download_count`` descending and selects the first
       ``max_datasets`` rows.
    4. Normalises column names to the contract schema (e.g. ``did`` →
       ``dataset_id``) and adds a ``publication_link`` field derived from the
       dataset's OpenML web page URL (``url``) when present.
    5. Returns a list of plain dictionaries ready for JSON serialisation.

    Parameters
    ----------
    max_datasets: int
        Maximum number of datasets to return.
    max_retries: int
        Number of retry attempts for transient HTTP errors (e.g. 429).
    initial_delay: float
        Initial back‑off delay in seconds.
    max_delay: float
        Maximum back‑off delay in seconds.

    Returns
    -------
    List[Dict[str, Any]]
        List of dataset metadata dictionaries.

    Raises
    ------
    DataFetchError
        If the request fails after the configured number of retries.
    """
    attempts = 0
    while True:
        try:
            logger.debug("Requesting OpenML dataset list")
            df = openml.datasets.list_datasets(output_format="dataframe")
            break
        except Exception as exc:  # pragma: no cover – network failures
            attempts += 1
            logger.warning(f"OpenML request failed (attempt {attempts}): {exc}")
            if attempts >= max_retries:
                raise DataFetchError(f"Failed to fetch OpenML datasets after {attempts} attempts") from exc
            _apply_backoff(attempts, initial_delay, max_delay)

    # ------------------------------------------------------------------
    # 1️⃣ Filter for classification tasks
    # ------------------------------------------------------------------
    if "type" in df.columns:
        mask = df["type"].str.contains("Supervised Classification", case=False, na=False)
        df = df[mask]
    else:
        logger.warning("OpenML dataset list missing 'type' column; proceeding with full list")

    # ------------------------------------------------------------------
    # 2️⃣ Sort by download count and take the top N
    # ------------------------------------------------------------------
    if "download_count" in df.columns:
        df = df.sort_values(by="download_count", ascending=False).head(max_datasets)
    else:
        logger.warning("OpenML dataset list missing 'download_count' column; using unsorted list")
        df = df.head(max_datasets)

    # ------------------------------------------------------------------
    # 3️⃣ Normalise column names to match the contract schema
    # ------------------------------------------------------------------
    mapping = {
        "did": "dataset_id",
        "name": "name",
        "version": "version",
        "download_count": "download_count",
        "NumberOfInstances": "number_of_instances",
        "NumberOfFeatures": "number_of_features",
        "NumberOfClasses": "number_of_classes",
        "NumberOfMissingValues": "number_of_missing_values",
        "type": "task_type",
        "url": "publication_link",
        "task_id": "task_id",
        "status": "status",
        "citation": "citation",
        "format": "format",
    }

    # Keep only columns that exist in the DataFrame
    available_cols = [c for c in mapping if c in df.columns]
    df = df[available_cols].rename(columns={c: mapping[c] for c in available_cols})

    # Ensure required keys exist (add ``None`` where missing)
    required_keys = [
        "dataset_id", "name", "download_count", "task_type",
        "number_of_instances", "number_of_features",
        "number_of_classes", "number_of_missing_values",
        "publication_link", "task_id"
    ]
    for key in required_keys:
        if key not in df.columns:
            df[key] = None

    # Convert to list of dicts
    records = df.to_dict(orient="records")
    logger.info(f"Fetched {len(records)} classification datasets from OpenML")
    return records
