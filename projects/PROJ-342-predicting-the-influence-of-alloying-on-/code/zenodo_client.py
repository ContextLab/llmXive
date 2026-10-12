"""
Zenodo client utilities for fetching public datasets.
This module provides a minimal wrapper around the Zenodo REST API to
retrieve a CSV file from a given DOI. It raises explicit exceptions so
that the ingestion pipeline can react appropriately.
"""

import io
from pathlib import Path

import pandas as pd
import requests


class DataUnavailableError(Exception):
    """Raised when data cannot be fetched from Zenodo."""
    pass


class DataInsufficientError(Exception):
    """Raised when the fetched dataset is empty or lacks required content."""
    pass


def fetch_from_zenodo(doi: str) -> pd.DataFrame:
    """
    Download a CSV file from a Zenodo record identified by its DOI.

    Parameters
    ----------
    doi: str
        Full DOI string, e.g. ``"10.5281/zenodo.10043838"``.

    Returns
    -------
    pd.DataFrame
        DataFrame containing the CSV data.

    Raises
    ------
    DataUnavailableError
        If the record cannot be retrieved, no CSV file is present, or the
        download fails.
    DataInsufficientError
        If the CSV is empty after loading.
    """
    # Extract the numeric record identifier from the DOI.
    try:
        record_id = doi.split(".")[-1]
    except Exception as exc:
        raise DataUnavailableError(f"Invalid DOI format: {doi}") from exc

    # Query Zenodo's public API for the record metadata.
    api_url = f"https://zenodo.org/api/records/{record_id}"
    response = requests.get(api_url, timeout=30)
    if response.status_code != 200:
        raise DataUnavailableError(
            f"Zenodo API request failed for record {record_id}: HTTP {response.status_code}"
        )

    record = response.json()
    files = record.get("files", [])

    # Locate the first CSV file in the record.
    csv_file = None
    for file_entry in files:
        filename = file_entry.get("key", "")
        if filename.lower().endswith(".csv"):
            csv_file = file_entry
            break

    if csv_file is None:
        raise DataUnavailableError(f"No CSV file found in Zenodo record {record_id}")

    # Resolve the download URL.
    download_url = csv_file.get("links", {}).get("download")
    if not download_url:
        # Fallback to the generic self link if a direct download link is missing.
        download_url = csv_file.get("links", {}).get("self")
    if not download_url:
        raise DataUnavailableError(f"Download link missing for CSV in record {record_id}")

    # Stream the CSV content.
    csv_resp = requests.get(download_url, timeout=30)
    if csv_resp.status_code != 200:
        raise DataUnavailableError(
            f"Failed to download CSV from {download_url}: HTTP {csv_resp.status_code}"
        )

    # Load the CSV into a DataFrame.
    try:
        df = pd.read_csv(io.BytesIO(csv_resp.content))
    except Exception as exc:
        raise DataUnavailableError(
            f"Failed to parse CSV from record {record_id}"
        ) from exc

    if df.empty:
        raise DataInsufficientError("Fetched CSV is empty.")

    return df
