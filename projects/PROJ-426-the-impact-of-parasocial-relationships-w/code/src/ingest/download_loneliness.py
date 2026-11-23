"""
Download the Reddit Loneliness Longitudinal Dataset from Zenodo.

This script fetches the dataset associated with the DOI provided in the
configuration, validates the presence of required columns, enforces that
each user has at least six distinct calendar months with non‑null UCLA
Loneliness scores, and writes the cleaned data to a Parquet file.
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, List
import requests
import pandas as pd

# Ensure the project's root is on the import path when the script is run
# directly (e.g. `python src/ingest/download_loneliness.py`).
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.utils.logging import (
    get_logger,
    log_stage_start,
    log_stage_end,
    log_error_context,
)
from src.utils.config import get_config
from src.utils.data_validation import record_checksum, ValidationError

# ----------------------------------------------------------------------
# Constants & configuration
# ----------------------------------------------------------------------
REQUIRED_COLUMNS = {
    "username_hash",
    "UCLA_Loneliness_Score",
    "timestamp",
    "baseline_text",
    "age",
    "gender",
}
MIN_USERS = 600            # Minimum number of rows after cleaning
MIN_MONTHS_PER_USER = 6    # Minimum distinct months with non‑null scores

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _extract_record_id_from_doi(doi: str) -> str:
    """
    Zenodo DOIs are of the form ``10.5281/zenodo.<record_id>``.
    This helper extracts the numeric record ID.
    """
    try:
        return doi.split(".")[-1]
    except Exception as exc:
        raise ValueError(f"Unable to extract record ID from DOI '{doi}': {exc}")


def _zenodo_api_get(record_id: str) -> Dict[str, Any]:
    """
    Retrieve the Zenodo metadata for a given record ID via the public API.
    """
    api_url = f"https://zenodo.org/api/records/{record_id}"
    response = requests.get(api_url, timeout=30)
    response.raise_for_status()
    return response.json()


def _choose_data_file(files: List[Dict[str, Any]]) -> Path:
    """
    From the list of files returned by the Zenodo API, pick the first
    one that looks like a data file (CSV, Parquet, or ZIP containing such).
    """
    for f in files:
        name = f.get("key", "")
        if name.lower().endswith((".csv", ".parquet", ".zip")):
            return Path(name)
    raise FileNotFoundError("No suitable data file found in Zenodo record.")


def fetch_dataset(zenodo_doi: str, download_dir: Path) -> Path:
    """
    Download the dataset file from Zenodo and return the local path to the
    downloaded file.

    Parameters
    ----------
    zenodo_doi : str
        DOI of the Zenodo record (e.g. ``10.5281/zenodo.1234567``).
    download_dir : Path
        Directory into which the file will be saved.

    Returns
    -------
    Path
        Path to the downloaded file.
    """
    logger.info(f"Fetching Zenodo record for DOI {zenodo_doi}")
    record_id = _extract_record_id_from_doi(zenodo_doi)
    meta = _zenodo_api_get(record_id)

    files = meta.get("files", [])
    if not files:
        raise FileNotFoundError("Zenodo record contains no files.")

    chosen = _choose_data_file(files)
    download_url = chosen.get("links", {}).get("download")
    if not download_url:
        raise RuntimeError(f"Download URL not found for file {chosen}")

    download_path = download_dir / chosen.name
    logger.info(f"Downloading {download_url} → {download_path}")

    with requests.get(download_url, stream=True, timeout=60) as r:
        r.raise_for_status()
        download_path.parent.mkdir(parents=True, exist_ok=True)
        with open(download_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    logger.info(f"Download completed: {download_path}")
    return download_path


def load_dataframe(file_path: Path) -> pd.DataFrame:
    """
    Load a CSV or Parquet file into a pandas DataFrame.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    if file_path.suffix.lower() == ".csv":
        df = pd.read_csv(file_path)
    elif file_path.suffix.lower() == ".parquet":
        df = pd.read_parquet(file_path)
    else:
        raise ValueError(f"Unsupported file extension: {file_path.suffix}")

    return df


def validate_columns(df: pd.DataFrame) -> None:
    """
    Ensure that the DataFrame contains all columns required for downstream
    processing.
    """
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")


def enforce_longitudinal_depth(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep only users that have at least ``MIN_MONTHS_PER_USER`` distinct
    calendar months with a non‑null UCLA Loneliness score.
    """
    # Ensure timestamp is datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    # Drop rows where timestamp or score is missing
    filtered = df.dropna(subset=["UCLA_Loneliness_Score", "timestamp"]).copy()
    filtered["year_month"] = filtered["timestamp"].dt.to_period("M")

    month_counts = (
        filtered.groupby("username_hash")["year_month"]
        .nunique()
        .reset_index(name="month_count")
    )
    eligible_users = month_counts.loc[
        month_counts["month_count"] >= MIN_MONTHS_PER_USER, "username_hash"
    ]

    kept = filtered[filtered["username_hash"].isin(eligible_users)].copy()
    # Drop the helper column before returning
    kept.drop(columns=["year_month"], inplace=True)
    return kept


def final_row_count_check(df: pd.DataFrame) -> None:
    """
    Verify that the cleaned dataset meets the minimum row count.
    """
    if len(df) < MIN_USERS:
        raise ValueError(
            f"Dataset contains {len(df)} rows after cleaning; "
            f"minimum required is {MIN_USERS}."
        )


def load_config() -> Dict[str, Any]:
    """
    Load configuration values.  If the project's ``src.utils.config``
    module is unavailable or does not define the expected keys, fall back
    to sensible defaults.
    """
    try:
        cfg = get_config()
        zenodo_doi = cfg.get("data", {}).get(
            "zenodo_loneliness_doi", "10.5281/zenodo.1234567"
        )
        output_path = Path(
            cfg.get("paths", {})
            .get("raw_loneliness_dataset", "data/raw/loneliness_dataset.parquet")
        )
    except Exception:
        # Graceful fallback – the script will still run; the DOI may be
        # invalid which will surface as an HTTP error.
        zenodo_doi = "10.5281/zenodo.1234567"
        output_path = Path("data/raw/loneliness_dataset.parquet")

    return {
        "zenodo_doi": zenodo_doi,
        "output_path": output_path,
    }


# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------


def main() -> None:
    """
    Orchestrates the download, validation, cleaning, and persistence of
    the Reddit Loneliness Longitudinal Dataset.
    """
    log_stage_start("T003: Download Reddit Loneliness Dataset")

    try:
        cfg = load_config()
        output_path: Path = Path(cfg["output_path"])
        checksum_path = output_path.parent / "loneliness_dataset.sha256"

        # Ensure the output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # ------------------------------------------------------------------
        # 1️⃣  Download the raw file from Zenodo
        # ------------------------------------------------------------------
        raw_file = fetch_dataset(cfg["zenodo_doi"], output_path.parent)

        # ------------------------------------------------------------------
        # 2️⃣  Load into a DataFrame
        # ------------------------------------------------------------------
        df = load_dataframe(raw_file)

        # ------------------------------------------------------------------
        # 3️⃣  Validate required columns
        # ------------------------------------------------------------------
        validate_columns(df)

        # ------------------------------------------------------------------
        # 4️⃣  Enforce longitudinal depth (≥6 months per user)
        # ------------------------------------------------------------------
        df_clean = enforce_longitudinal_depth(df)

        # ------------------------------------------------------------------
        # 5️⃣  Final row‑count sanity check (≥600 rows)
        # ------------------------------------------------------------------
        final_row_count_check(df_clean)

        # ------------------------------------------------------------------
        # 6️⃣  Persist as Parquet and record checksum
        # ------------------------------------------------------------------
        logger.info(f"Writing cleaned dataset to {output_path}")
        df_clean.to_parquet(output_path, index=False)
        record_checksum(output_path, checksum_path)

        log_stage_end("T003: Download Reddit Loneliness Dataset – Success")
    except Exception as exc:
        log_error_context("T003: Download Reddit Loneliness Dataset – Failed", exc)
        raise

if __name__ == "__main__":
    main()
