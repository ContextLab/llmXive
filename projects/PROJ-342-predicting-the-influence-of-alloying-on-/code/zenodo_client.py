"""
Zenodo client utilities for fetching dataset CSV files by DOI.

This module provides:
- DataUnavailableError: raised when no suitable CSV file can be retrieved.
- DataInsufficientError: raised when the fetched dataset is empty.
- fetch_from_zenodo(doi: str) -> pandas.DataFrame: download the first CSV file
  attached to the Zenodo record identified by the DOI and return it as a DataFrame.

The implementation uses the public Zenodo REST API (https://zenodo.org/api/records/<id>).
It streams the CSV file to avoid loading the entire file into memory at once,
then reads it with pandas.read_csv.  Any HTTP or parsing errors are wrapped in
DataUnavailableError so that the ingestion pipeline can fall back to an alternate
DOI as specified in ``code/ingest.py``.
"""

import json
import logging
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

__all__ = [
    "DataUnavailableError",
    "DataInsufficientError",
    "fetch_from_zenodo",
]


class DataUnavailableError(RuntimeError):
    """Raised when a CSV file cannot be retrieved from a Zenodo record."""
    pass


class DataInsufficientError(RuntimeError):
    """Raised when the retrieved dataset is empty."""
    pass


def _extract_record_id(doi: str) -> str:
    """
    Extract the numeric record identifier from a Zenodo DOI.

    Example:
        doi = "10.5281/zenodo.10043838" -> "10043838"
    """
    try:
        return doi.rsplit(".", 1)[-1]
    except Exception as exc:
        raise DataUnavailableError(f"Unable to parse record id from DOI '{doi}': {exc}") from exc


def _get_record_metadata(record_id: str) -> dict:
    """
    Retrieve the Zenodo record metadata as a JSON dict.

    Parameters
    ----------
    record_id: str
        The numeric Zenodo record identifier.

    Returns
    -------
    dict
        The JSON representation of the record metadata.
    """
    api_url = f"https://zenodo.org/api/records/{record_id}"
    response = requests.get(api_url, timeout=30)
    if not response.ok:
        raise DataUnavailableError(
            f"Failed to fetch Zenodo record metadata (status {response.status_code}) for record {record_id}"
        )
    return response.json()


def _select_csv_file(metadata: dict) -> Optional[dict]:
    """
    From the Zenodo metadata, select the first file entry that ends with '.csv'.

    Returns
    -------
    dict or None
        The file entry dict if a CSV file is found, otherwise None.
    """
    files = metadata.get("files", [])
    for file_entry in files:
        filename = file_entry.get("key", "")
        if filename.lower().endswith(".csv"):
            return file_entry
    return None


def _download_csv(file_entry: dict, target_path: Path) -> None:
    """
    Stream‑download a CSV file from Zenodo to ``target_path``.

    Parameters
    ----------
    file_entry: dict
        The Zenodo file entry containing download links.
    target_path: Path
        Destination path for the downloaded CSV.
    """
    download_url = file_entry.get("links", {}).get("self")
    if not download_url:
        raise DataUnavailableError("CSV file entry does not contain a download URL.")

    # Stream download to avoid loading the whole file into memory.
    with requests.get(download_url, stream=True, timeout=60) as r:
        r.raise_for_status()
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with target_path.open("wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:  # filter out keep‑alive chunks
                    f.write(chunk)


def fetch_from_zenodo(doi: str) -> pd.DataFrame:
    """
    Fetch the first CSV file attached to a Zenodo record identified by ``doi``.

    The function:
    1. Resolves the record identifier from the DOI.
    2. Queries the Zenodo REST API for the record metadata.
    3. Finds the first file ending with ``.csv``.
    4. Downloads that file to a temporary location.
    5. Loads the CSV into a pandas DataFrame and returns it.

    If the record does not contain a CSV file, or any network error occurs,
    a ``DataUnavailableError`` is raised.  If the CSV loads but is empty,
    a ``DataInsufficientError`` is raised.

    Parameters
    ----------
    doi: str
        The Zenodo DOI (e.g., ``"10.5281/zenodo.10043838"``).

    Returns
    -------
    pandas.DataFrame
        The dataset contained in the CSV file.

    Raises
    ------
    DataUnavailableError
        When the DOI cannot be resolved, the record lacks a CSV, or the download fails.
    DataInsufficientError
        When the downloaded CSV contains no rows.
    """
    logger = logging.getLogger(__name__)

    logger.info(f"Resolving Zenodo DOI: {doi}")
    record_id = _extract_record_id(doi)

    logger.debug(f"Zenodo record ID resolved to {record_id}")

    metadata = _get_record_metadata(record_id)

    csv_file_entry = _select_csv_file(metadata)
    if csv_file_entry is None:
        raise DataUnavailableError(f"No CSV file found in Zenodo record {record_id}")

    # Use a temporary file inside the project ``data/raw`` directory.
    raw_dir = Path(__file__).resolve().parent.parent / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    temp_csv_path = raw_dir / f"zenodo_{record_id}.csv"

    logger.info(f"Downloading CSV to temporary path: {temp_csv_path}")
    _download_csv(csv_file_entry, temp_csv_path)

    try:
        df = pd.read_csv(temp_csv_path)
    except Exception as exc:
        raise DataUnavailableError(f"Failed to read CSV from Zenodo record {record_id}: {exc}") from exc

    if df.empty:
        raise DataInsufficientError(f"The CSV file from Zenodo record {record_id} is empty.")

    # Normalise column names to match the ingestion pipeline expectations.
    # The original schema (specs/.../dataset.schema.yaml) uses ``tg_value`` and
    # ``elements``.  Downstream code expects ``Tg`` and ``composition``.
    # We perform a minimal mapping that covers the most common cases.
    rename_map = {}
    if "tg_value" in df.columns:
        rename_map["tg_value"] = "Tg"
    if "Tg" in df.columns:
        rename_map["Tg"] = "Tg"  # identity, kept for clarity
    if "composition" in df.columns:
        rename_map["composition"] = "composition"
    if "elements" in df.columns:
        # ``elements`` is a JSON‑like mapping; convert to a simple string
        # representation that the descriptor code can later parse.
        def _elements_to_str(elem):
            if isinstance(elem, str):
                return elem
            try:
                # Assume dict-like mapping {symbol: fraction}
                return "".join(f"{k}{v:.3f}" for k, v in sorted(elem.items()))
            except Exception:
                return str(elem)

        df["composition"] = df["elements"].apply(_elements_to_str)
        rename_map["elements"] = "composition"

    if rename_map:
        logger.debug(f"Renaming columns as per mapping: {rename_map}")
        df = df.rename(columns=rename_map)

    logger.info(f"Successfully fetched and loaded data from DOI {doi} (rows: {len(df)})")
    return df
