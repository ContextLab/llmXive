"""
Minimal Zenodo client used by the ingestion pipeline.
It fetches a CSV file from a Zenodo record given its DOI, streams the
download to a temporary file, loads it into a pandas DataFrame and performs
a small amount of column normalisation so that the rest of the pipeline can
operate on a consistent schema (e.g. ``Tg`` column).
"""
import json
import os
from pathlib import Path
from typing import Any

import pandas as pd
import requests

class DataUnavailableError(Exception):
    """Raised when a Zenodo record cannot be accessed or contains no CSV."""
    pass

class DataInsufficientError(Exception):
    """Raised when a fetched dataset is empty or otherwise unusable."""
    pass

def _doi_to_record_id(doi: str) -> str:
    """
    Convert a Zenodo DOI of the form ``10.5281/zenodo.<id>`` to the numeric
    record identifier.
    """
    if not doi.startswith("10.5281/zenodo."):
        raise DataUnavailableError(f"Unsupported DOI format: {doi}")
    return doi.split(".")[-1]

def fetch_from_zenodo(doi: str) -> pd.DataFrame:
    """
    Fetch the first CSV file attached to a Zenodo record.

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
        If the record cannot be reached, does not contain a CSV, or the
        download fails.
    DataInsufficientError
        If the downloaded CSV is empty.
    """
    record_id = _doi_to_record_id(doi)
    api_url = f"https://zenodo.org/api/records/{record_id}"
    try:
        resp = requests.get(api_url, timeout=30)
        resp.raise_for_status()
    except Exception as exc:
        raise DataUnavailableError(f"Failed to retrieve Zenodo metadata for DOI {doi}: {exc}") from exc

    meta = resp.json()
    files = meta.get("files", [])
    csv_file_meta = None
    for f in files:
        filename = f.get("key", "")
        if filename.lower().endswith(".csv"):
            csv_file_meta = f
            break

    if csv_file_meta is None:
        raise DataUnavailableError("No CSV file found in Zenodo record.")

    download_url = csv_file_meta.get("links", {}).get("download")
    if not download_url:
        raise DataUnavailableError("Download link for CSV not found in Zenodo metadata.")

    # Stream the download to a temporary location inside the project ``data/raw`` folder.
    raw_dir = Path(__file__).resolve().parent.parent / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    temp_path = raw_dir / f"zenodo_{record_id}.csv"

    try:
        with requests.get(download_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(temp_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
    except Exception as exc:
        raise DataUnavailableError(f"Failed to download CSV from Zenodo: {exc}") from exc

    # Load into pandas
    try:
        df = pd.read_csv(temp_path)
    except Exception as exc:
        raise DataUnavailableError(f"Unable to parse CSV file downloaded from Zenodo: {exc}") from exc

    if df.empty:
        raise DataInsufficientError("Downloaded CSV is empty.")

    # Normalise column names expected by downstream code
    if "tg_value" in df.columns and "Tg" not in df.columns:
        df = df.rename(columns={"tg_value": "Tg"})
    # Some datasets use ``composition``; if they provide an ``elements`` mapping
    # we keep it untouched – downstream validation will simply warn.
    return df
