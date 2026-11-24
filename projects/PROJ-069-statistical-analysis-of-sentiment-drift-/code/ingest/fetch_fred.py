"""
fetch_fred.py
----------------
Downloads macro‑economic series from the official FRED API and writes them to CSV
files under ``data/raw/fred/``.  It also records SHA‑256 checksums for each CSV in
``data/checksums.json`` and logs the source URLs in ``results/fred_download_log.json``.

The script is intended to be executed via:
    python -m code.ingest.fetch_fred

It aborts loudly if the required FRED API key is missing or if any download fails.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List

import pandas as pd
from fredapi import Fred

# Project utilities
from llmxive_toolkit import paths, get_logger
from config import get_fred_api_key

log = get_logger(__name__)


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _sha256_of_file(file_path: Path) -> str:
    """Compute the SHA‑256 hash of a file."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _update_checksums(checksum_path: Path, new_entries: Dict[str, str]) -> None:
    """
    Load (or create) a JSON checksum file and merge ``new_entries``.

    The JSON structure is a simple mapping ``relative_path -> sha256``.
    """
    if checksum_path.exists():
        with checksum_path.open("r", encoding="utf-8") as f:
            checksums = json.load(f)
    else:
        checksums = {}

    checksums.update(new_entries)

    with checksum_path.open("w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2, sort_keys=True)


def _log_download(log_path: Path, entries: List[Dict[str, str]]) -> None:
    """
    Write a JSON log of the download URLs.

    The file contains a list of objects, each with the keys:
    ``series_id`` and ``url``.
    """
    with log_path.open("w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, sort_keys=True)


# ----------------------------------------------------------------------
# Core download logic
# ----------------------------------------------------------------------
def download_series(
    fred: Fred,
    series_id: str,
    output_path: Path,
    url_template: str = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
) -> None:
    """
    Download a single series from FRED and write it to ``output_path``.

    The function:
    1. Retrieves the series as a ``pandas.Series``.
    2. Resets the index to obtain a ``date`` column.
    3. Writes the DataFrame to CSV (with ``date`` and ``value`` columns).

    Parameters
    ----------
    fred: Fred
        Authenticated ``fredapi.Fred`` client.
    series_id: str
        Official FRED series identifier (e.g., ``GDP``).
    output_path: Path
        Destination CSV file.
    url_template: str
        Template used to construct the public CSV URL for logging.
    """
    log.info(f"Fetching series {series_id} from FRED")
    try:
        series = fred.get_series(series_id)
    except Exception as exc:
        log.error(f"Failed to fetch series {series_id}: {exc}")
        raise

    if series.empty:
        raise ValueError(f"Series {series_id} returned no data")

    # Ensure the index is a datetime index
    if not isinstance(series.index, pd.DatetimeIndex):
        series.index = pd.to_datetime(series.index)

    df = series.reset_index()
    df.columns = ["date", "value"]

    # Guarantee the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    log.info(f"Wrote {series_id} to {output_path}")


def main() -> None:
    """
    Entry point for the module.

    Steps performed:
    1. Load the FRED API key from the environment.
    2. Initialise a ``fredapi.Fred`` client.
    3. Download the three required series.
    4. Compute and record SHA‑256 checksums.
    5. Write a JSON log of the source URLs.
    """
    # ------------------------------------------------------------------
    # 1. Retrieve API key
    # ------------------------------------------------------------------
    api_key = get_fred_api_key()
    log.info("Using provided FRED API key")

    # ------------------------------------------------------------------
    # 2. Initialise client
    # ------------------------------------------------------------------
    fred = Fred(api_key=api_key)

    # ------------------------------------------------------------------
    # 3. Define series and destination files
    # ------------------------------------------------------------------
    series_info = {
        "GDP": {
            "filename": "fred_gdp.csv",
            "url": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=GDP",
        },
        "UNRATE": {
            "filename": "fred_unrate.csv",
            "url": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=UNRATE",
        },
        "CSCICP03": {
            "filename": "fred_consumer_confidence.csv",
            "url": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=CSCICP03",
        },
    }

    # ------------------------------------------------------------------
    # 4. Download each series
    # ------------------------------------------------------------------
    download_log: List[Dict[str, str]] = []
    checksum_entries: Dict[str, str] = {}

    for series_id, meta in series_info.items():
        output_path = paths.data("raw", "fred", meta["filename"])
        download_series(fred, series_id, output_path, url_template=meta["url"])

        # Record checksum (relative path as stored in the repo)
        rel_path = str(output_path.relative_to(paths.root))
        checksum_entries[rel_path] = _sha256_of_file(output_path)

        # Record log entry
        download_log.append({"series_id": series_id, "url": meta["url"]})

    # ------------------------------------------------------------------
    # 5. Persist checksums
    # ------------------------------------------------------------------
    checksums_path = paths.data("checksums.json")
    _update_checksums(checksums_path, checksum_entries)
    log.info(f"Updated checksum file at {checksums_path}")

    # ------------------------------------------------------------------
    # 6. Persist download log
    # ------------------------------------------------------------------
    log_path = paths.results("fred_download_log.json")
    _log_download(log_path, download_log)
    log.info(f"Download log written to {log_path}")


if __name__ == "__main__":
    # When executed as a script ``python -m code.ingest.fetch_fred``
    # we run the main routine and let any exception propagate so that
    # the CI / runner can see a non‑zero exit status.
    main()
