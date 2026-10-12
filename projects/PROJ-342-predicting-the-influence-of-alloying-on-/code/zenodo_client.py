"""
Zenodo client utilities for fetching CSV datasets by DOI.

This module provides:
- DataUnavailableError: raised when the dataset cannot be retrieved.
- DataInsufficientError: raised when the retrieved dataset is empty.
- fetch_from_zenodo(doi: str) -> pandas.DataFrame: fetches the first CSV
  file from the Zenodo record identified by the DOI and returns it as a
  DataFrame.

The implementation uses the public Zenodo REST API
(https://zenodo.org/api/records/<record_id>) to obtain metadata,
selects a CSV file from the record, streams the download to a temporary
file, loads it with pandas, and cleans up the temporary file.
All network errors are converted to DataUnavailableError so that the
ingestion pipeline can handle fallback logic uniformly.
"""

import os
import json
from pathlib import Path
from typing import Optional

import requests
import pandas as pd

__all__ = [
    "DataUnavailableError",
    "DataInsufficientError",
    "fetch_from_zenodo",
]


class DataUnavailableError(Exception):
    """Raised when a Zenodo record or its CSV file cannot be accessed."""
    pass


class DataInsufficientError(Exception):
    """Raised when a retrieved dataset is empty or otherwise unusable."""
    pass


def _doi_to_record_id(doi: str) -> str:
    """
    Convert a Zenodo DOI of the form ``10.5281/zenodo.<id>`` to the numeric
    record identifier used by the Zenodo API.

    Parameters
    ----------
    doi: str
        The DOI string.

    Returns
    -------
    str
        The numeric record identifier.
    """
    # The DOI may contain a trailing version (e.g. ``10.5281/zenodo.10043838.v1``);
    # we keep only the numeric part after the last dot.
    parts = doi.rstrip("/").split(".")
    record_id = parts[-1]
    # In case a version suffix is present (e.g. ``10043838v1``), strip non‑digits.
    record_id = "".join(filter(str.isdigit, record_id))
    if not record_id.isdigit():
        raise DataUnavailableError(f"Unable to extract record ID from DOI '{doi}'.")
    return record_id


def _select_csv_file(record_json: dict) -> Optional[dict]:
    """
    From the Zenodo record JSON, select the first file whose filename ends
    with ``.csv`` (case‑insensitive). Returns the file dictionary or ``None``
    if no CSV is present.
    """
    files = record_json.get("files", [])
    for file_entry in files:
        filename = file_entry.get("filename", "")
        if filename.lower().endswith(".csv"):
            return file_entry
    return None


def fetch_from_zenodo(doi: str) -> pd.DataFrame:
    """
    Fetch the first CSV file associated with a Zenodo DOI.

    The function:
    1. Resolves the DOI to a Zenodo record identifier.
    2. Queries the Zenodo REST API for the record metadata.
    3. Identifies a CSV file in the record.
    4. Streams the CSV to a temporary file on disk.
    5. Loads the CSV into a pandas DataFrame and returns it.

    Parameters
    ----------
    doi: str
        The Zenodo DOI (e.g. ``10.5281/zenodo.10043838``).

    Returns
    -------
    pandas.DataFrame
        The contents of the CSV file.

    Raises
    ------
    DataUnavailableError
        If the record cannot be fetched, no CSV is present, or the download
        fails.
    DataInsufficientError
        If the CSV is successfully downloaded but contains no rows.
    """
    record_id = _doi_to_record_id(doi)
    api_url = f"https://zenodo.org/api/records/{record_id}"

    try:
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        raise DataUnavailableError(f"Failed to retrieve Zenodo record metadata for DOI {doi}: {exc}") from exc

    try:
        record_json = response.json()
    except json.JSONDecodeError as exc:
        raise DataUnavailableError(f"Invalid JSON metadata for DOI {doi}: {exc}") from exc

    csv_file_entry = _select_csv_file(record_json)
    if csv_file_entry is None:
        raise DataUnavailableError("No CSV file found in Zenodo record metadata.")

    # Prefer the direct download link; fallback to the generic self link.
    download_url = csv_file_entry.get("links", {}).get("download")
    if not download_url:
        download_url = csv_file_entry.get("links", {}).get("self")
    if not download_url:
        raise DataUnavailableError("CSV file entry lacks a downloadable URL.")

    # Stream the CSV to a temporary location.
    temp_dir = Path.cwd()
    temp_path = temp_dir / f"zenodo_{record_id}_tmp.csv"
    try:
        with requests.get(download_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(temp_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep‑alive chunks
                        f.write(chunk)
    except Exception as exc:
        # Clean up any partially written file before propagating the error.
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
        raise DataUnavailableError(f"Failed to download CSV from {download_url}: {exc}") from exc

    try:
        df = pd.read_csv(temp_path)
    except Exception as exc:
        raise DataUnavailableError(f"Failed to parse CSV downloaded from {download_url}: {exc}") from exc
    finally:
        # Ensure the temporary file is removed irrespective of success.
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)

    if df.empty:
        raise DataInsufficientError("The retrieved CSV file is empty.")

    return df
