"""
Zenodo client utilities for fetching CSV datasets from Zenodo records.
Provides:
  - DataUnavailableError: raised when a CSV cannot be retrieved.
  - DataInsufficientError: raised when the retrieved dataset is empty.
  - fetch_from_zenodo(doi: str) -> pandas.DataFrame
The implementation uses the public Zenodo REST API (no authentication required)
and streams the CSV file to avoid excessive memory usage.
"""

import io
import logging
from pathlib import Path
from typing import Tuple

import pandas as pd
import requests

logger = logging.getLogger(__name__)


class DataUnavailableError(Exception):
    """Raised when a Zenodo record cannot be accessed or contains no CSV file."""
    pass


class DataInsufficientError(Exception):
    """Raised when the fetched dataset is empty after download."""
    pass


def _extract_record_id(doi: str) -> str:
    """
    Extract the numeric record identifier from a Zenodo DOI.
    Expected format: ``10.5281/zenodo.<record_id>``.
    """
    try:
        # Split on the last dot; the part after is the record id.
        return doi.rsplit(".", 1)[-1]
    except Exception as exc:
        raise DataUnavailableError(f"Unable to parse record ID from DOI '{doi}': {exc}") from exc


def _get_record_metadata(record_id: str) -> dict:
    """
    Retrieve Zenodo record metadata via the public API.
    """
    api_url = f"https://zenodo.org/api/records/{record_id}"
    response = requests.get(api_url, timeout=30)
    if response.status_code != 200:
        raise DataUnavailableError(
            f"Failed to fetch Zenodo record metadata (status {response.status_code}) for record {record_id}"
        )
    return response.json()


def _select_csv_file(metadata: dict) -> Tuple[str, str]:
    """
    From the Zenodo record metadata, select the first file ending with ``.csv``.
    Returns a tuple ``(filename, download_url)``.
    """
    files = metadata.get("files", [])
    for file_info in files:
        filename = file_info.get("key") or file_info.get("filename")
        if filename and filename.lower().endswith(".csv"):
            # The direct download link is provided under ``links`` -> ``self``.
            # ``self`` points to the file endpoint; we can use it for streaming.
            download_url = file_info.get("links", {}).get("self")
            if download_url:
                return filename, download_url
    raise DataUnavailableError("No CSV file found in Zenodo record metadata.")


def fetch_from_zenodo(doi: str) -> pd.DataFrame:
    """
    Fetch a CSV dataset from a Zenodo DOI.

    Parameters
    ----------
    doi: str
        Full Zenodo DOI (e.g., ``10.5281/zenodo.10043838``).

    Returns
    -------
    pandas.DataFrame
        DataFrame constructed from the CSV content.

    Raises
    ------
    DataUnavailableError
        If the record cannot be accessed or does not contain a CSV file.
    DataInsufficientError
        If the CSV is retrieved but contains no rows.
    """
    logger.info(f"Fetching dataset from Zenodo DOI: {doi}")
    record_id = _extract_record_id(doi)

    # 1️⃣ Retrieve metadata
    metadata = _get_record_metadata(record_id)

    # 2️⃣ Identify CSV file
    filename, download_url = _select_csv_file(metadata)
    logger.info(f"Identified CSV file '{filename}' for download.")

    # 3️⃣ Stream download
    with requests.get(download_url, stream=True, timeout=60) as r:
        if r.status_code != 200:
            raise DataUnavailableError(
                f"Failed to download CSV '{filename}' (status {r.status_code})."
            )
        # Use BytesIO to accumulate streamed bytes without loading entire file into RAM.
        buffer = io.BytesIO()
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:  # filter out keep-alive chunks
                buffer.write(chunk)
        buffer.seek(0)

    # 4️⃣ Load into pandas (let pandas handle compression detection if any)
    try:
        df = pd.read_csv(buffer)
    except Exception as exc:
        raise DataUnavailableError(f"Pandas failed to parse the CSV from DOI {doi}: {exc}") from exc

    if df.empty:
        raise DataInsufficientError("Fetched CSV is empty.")

    logger.info(f"Successfully fetched {len(df)} rows from DOI {doi}.")
    return df
