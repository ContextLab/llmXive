"""
ACE data fetcher.

Downloads ACE SWEPAM (proton density, temperature) and SWICS (helium
abundance) Level‑2 data for a given date range from the NASA CDAWeb public
API, merges them, and writes a combined CSV containing the required columns:
`N_p`, `T_p`, `He2+_ratio`.

The file is saved as `data/raw/ace_<YYYYMM>.csv`.
"""

import time
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict

import pandas as pd
import requests
from io import StringIO

from code.config import RAW_DATA_DIR
from code import logger

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _exponential_backoff(attempt: int, base: float = 1.0) -> None:
    """Sleep ``base * 2**attempt`` seconds."""
    time.sleep(base * (2 ** attempt))

def _download_text(url: str, params: Dict = None) -> str:
    """
    Download a text file via HTTP/HTTPS and return its content.

    Parameters
    ----------
    url : str
        The base URL to request.
    params : dict, optional
        Query parameters passed to ``requests.get``.  If ``None`` the request
        is made without query parameters.

    Returns
    -------
    str
        The response body as text.

    Raises
    ------
    ConnectionError
        If the request fails after three attempts.
    """
    headers = {"User-Agent": "Mozilla/5.0 (compatible; llmXive/1.0)"}
    for attempt in range(3):
        try:
            response = requests.get(url, params=params, timeout=60, stream=True, headers=headers)
            response.raise_for_status()
            return response.text
        except Exception as exc:  # pragma: no cover – exercised by CI when network fails
            logger.warning(f"Attempt {attempt + 1} failed for {url} with params {params}: {exc}")
            if attempt == 2:
                raise ConnectionError(f"Unable to download {url} with params {params}") from exc
            _exponential_backoff(attempt)
    raise ConnectionError(f"Failed to download {url} with params {params}")

def _parse_cdaweb_csv(csv_text: str, required_cols: List[str]) -> pd.DataFrame:
    """
    Parse CSV text returned by the CDAWeb ``Download`` service.

    The service always includes a column named ``Epoch`` (ISO‑8601 timestamps).
    This function converts that column to a ``datetime`` called ``timestamp``,
    selects the required data columns, and returns a tidy DataFrame.
    """
    df = pd.read_csv(StringIO(csv_text))
    if "Epoch" not in df.columns:
        raise ConnectionError("CDAWeb CSV does not contain an 'Epoch' column.")
    df = df.rename(columns={"Epoch": "timestamp"})
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

    missing = set(required_cols) - set(df.columns)
    if missing:
        raise ConnectionError(f"Missing required columns in CDAWeb download: {missing}")

    return df[["timestamp"] + required_cols]

# ----------------------------------------------------------------------
# Main public function
# ----------------------------------------------------------------------
def fetch_ace(start_date: str, end_date: str) -> str:
    """
    Fetch ACE solar‑wind composition data for the supplied date range.

    The function downloads two separate CDAWeb datasets:
    * ``ace/swepam`` for proton density (``N_p``) and temperature (``T_p``)
    * ``ace/swics`` for helium abundance (``He2+_ratio``)

    The two tables are merged on the exact timestamps and written to
    ``data/raw/ace_<YYYYMM>.csv`` where ``YYYYMM`` corresponds to the month
    of ``start_date`` (as required by the specification).

    Parameters
    ----------
    start_date : str
        Start date in ``YYYY‑MM‑DD`` format (inclusive).
    end_date : str
        End date in ``YYYY‑MM‑DD`` format (inclusive).

    Returns
    -------
    str
        Path to the written CSV file.
    """
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt   = datetime.strptime(end_date,   "%Y-%m-%d")

    # Output file – month of the start date per spec
    yyyymm = start_dt.strftime("%Y%m")
    output_path = Path(RAW_DATA_DIR) / f"ace_{yyyymm}.csv"

    # ------------------------------------------------------------------
    # 1. Download SWEpam (N_p, T_p)
    # ------------------------------------------------------------------
    swepam_params = {
        "dataset": "ace/swepam",
        "variables": "N_p,T_p",
        "start": start_dt.strftime("%Y-%m-%d"),
        "stop":  end_dt.strftime("%Y-%m-%d"),
        "format": "csv"
    }
    logger.debug(f"Requesting ACE SWEpam data with params: {swepam_params}")
    swepam_txt = _download_text("https://cdaweb.gsfc.nasa.gov/WS/v1/Download", swepam_params)
    swepam_df = _parse_cdaweb_csv(swepam_txt, ["N_p", "T_p"])

    # ------------------------------------------------------------------
    # 2. Download SWICS (He2+_ratio)
    # ------------------------------------------------------------------
    swics_params = {
        "dataset": "ace/swics",
        "variables": "He2+_ratio",
        "start": start_dt.strftime("%Y-%m-%d"),
        "stop":  end_dt.strftime("%Y-%m-%d"),
        "format": "csv"
    }
    logger.debug(f"Requesting ACE SWICS data with params: {swics_params}")
    swics_txt = _download_text("https://cdaweb.gsfc.nasa.gov/WS/v1/Download", swics_params)
    swics_df = _parse_cdaweb_csv(swics_txt, ["He2+_ratio"])

    # ------------------------------------------------------------------
    # 3. Merge on timestamp (inner join keeps rows where both instruments have data)
    # ------------------------------------------------------------------
    merged = pd.merge(swepam_df, swics_df, on="timestamp", how="inner")

    if merged.empty:
        raise ConnectionError(f"No overlapping ACE data found for period {start_date}–{end_date}")

    # ------------------------------------------------------------------
    # 4. Write CSV
    # ------------------------------------------------------------------
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(output_path, index=False)
    logger.info(f"ACE data written to {output_path}")

    return str(output_path)

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch ACE solar‑wind composition data.")
    parser.add_argument("--start", required=True, help="Start date in YYYY‑MM‑DD")
    parser.add_argument("--end",   required=True, help="End date in YYYY‑MM‑DD")
    args = parser.parse_args()

    try:
        path = fetch_ace(args.start, args.end)
        print(f"ACE data saved to: {path}")
    except Exception as exc:  # pragma: no cover – exercised by CI when network fails
        logger.error(f"Failed to fetch ACE data: {exc}")
        raise
