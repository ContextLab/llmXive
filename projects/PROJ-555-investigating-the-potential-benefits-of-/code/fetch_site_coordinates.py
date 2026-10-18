import logging
import json
import sys
import zipfile
from pathlib import Path
from datetime import datetime
from typing import List

import pandas as pd
import requests

# Project utilities
from llmxive_toolkit import paths, get_logger
from config import ensure_directories
from data_acquisition import log_api_query

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Logger setup (uses the project's logging configuration if any)
# ----------------------------------------------------------------------
def setup_logger(name: str) -> logging.Logger:
    """
    Setup a logger for this module.

    Parameters
    ----------
    name : str
        Name of the logger (usually ``__name__``).

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    return get_logger(name)

# ----------------------------------------------------------------------
# WDPA download
# ----------------------------------------------------------------------
WDPA_DOWNLOAD_URL = "https://dopa-explorer.jrc.ec.europa.eu/download?type=wdpa&format=ZIP"

def download_wdpa_release(output_dir: Path) -> Path:
    """
    Downloads the latest WDPA release (ZIP) from the official source.

    Parameters
    ----------
    output_dir : Path
        Directory where the ZIP file will be saved.

    Returns
    -------
    Path
        Path to the downloaded ZIP file.

    Raises
    ------
    RuntimeError
        If the HTTP request fails.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / "WDPA.zip"

    logger.info(f"Downloading WDPA data from {WDPA_DOWNLOAD_URL}")
    try:
        response = requests.get(WDPA_DOWNLOAD_URL, stream=True, timeout=120)
        # Log the request
        log_api_query(
            {"url": WDPA_DOWNLOAD_URL, "method": "GET"},
            version="1.0.0"
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"Failed to download WDPA data: HTTP {response.status_code}"
            )
        # Write to file in chunks
        with open(zip_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        logger.info(f"WDPA zip saved to {zip_path}")
        return zip_path
    except Exception as e:
        # Write error details to fetch_error.log and re‑raise
        error_log = paths.data("raw", "fetch_error.log")
        error_log.parent.mkdir(parents=True, exist_ok=True)
        with open(error_log, "a") as log_f:
            log_f.write(
                f"{datetime.utcnow().isoformat()} - WDPA download error: {e}\\n"
            )
        raise RuntimeError(f"WDPA download failed: {e}") from e

# ----------------------------------------------------------------------
# Extract and load CSV
# ----------------------------------------------------------------------
def extract_and_load_wdpa(zip_path: Path) -> pd.DataFrame:
    """
    Extracts the CSV file from the WDPA ZIP archive and loads it into a
    DataFrame.

    Parameters
    ----------
    zip_path : Path
        Path to the downloaded WDPA ZIP file.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing the WDPA records.

    Raises
    ------
    RuntimeError
        If extraction or loading fails.
    """
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            # Find the first CSV file inside the archive
            csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
            if not csv_names:
                raise RuntimeError("No CSV file found inside WDPA ZIP archive.")
            csv_name = csv_names[0]
            logger.info(f"Extracting {csv_name} from {zip_path}")
            with zf.open(csv_name) as csv_file:
                df = pd.read_csv(csv_file, low_memory=False)
        logger.info(f"Loaded WDPA CSV with {len(df)} rows")
        return df
    except Exception as e:
        error_log = paths.data("raw", "fetch_error.log")
        error_log.parent.mkdir(parents=True, exist_ok=True)
        with open(error_log, "a") as log_f:
            log_f.write(
                f"{datetime.utcnow().isoformat()} - WDPA extraction error: {e}\\n"
            )
        raise RuntimeError(f"Failed to extract/load WDPA data: {e}") from e

# ----------------------------------------------------------------------
# Filtering / sampling
# ----------------------------------------------------------------------
def filter_and_sample_sites(df: pd.DataFrame, target_count: int = 30) -> pd.DataFrame:
    """
    Filters the WDPA DataFrame for rows that contain the required metadata
    and samples up to ``target_count`` sites.

    Required columns (case‑insensitive):
    - WDPAID (site identifier)
    - DESIG_TYPE (site type / designation)
    - LATITUDE
    - LONGITUDE
    - BIOME
    - DESIG_STATUS (protection status)

    Parameters
    ----------
    df : pandas.DataFrame
        Raw WDPA DataFrame.
    target_count : int, optional
        Desired number of sites (default is 30).

    Returns
    -------
    pandas.DataFrame
        Filtered and sampled DataFrame with the columns renamed to the
        project‑specific schema.
    """
    # Normalise column names to upper case for easier handling
    df_cols = {c.upper(): c for c in df.columns}
    required = ["WDPAID", "DESIG_TYPE", "LATITUDE", "LONGITUDE", "BIOME", "DESIG_STATUS"]
    missing = [c for c in required if c not in df_cols]
    if missing:
        raise RuntimeError(f"WDPA data is missing required columns: {missing}")

    # Select and rename columns
    selected = df.loc[
        df[df_cols["LATITUDE"]].notna() & df[df_cols["LONGITUDE"]].notna()
    ].copy()
    selected = selected[[
        df_cols["WDPAID"],
        df_cols["DESIG_TYPE"],
        df_cols["LATITUDE"],
        df_cols["LONGITUDE"],
        df_cols["BIOME"],
        df_cols["DESIG_STATUS"],
    ]]

    # Rename to project schema
    selected = selected.rename(columns={
        df_cols["WDPAID"]: "site_id",
        df_cols["DESIG_TYPE"]: "site_type",
        df_cols["LATITUDE"]: "latitude",
        df_cols["LONGITUDE"]: "longitude",
        df_cols["BIOME"]: "biome",
        df_cols["DESIG_STATUS"]: "protection_status",
    })

    # Add placeholder pairing_id column (empty string for now)
    selected["pairing_id"] = ""

    # Drop rows with any remaining nulls in required fields
    selected = selected.dropna(subset=["site_id", "site_type", "latitude", "longitude", "biome", "protection_status"])

    # Sample without replacement; if fewer rows than target, keep all
    if len(selected) > target_count:
        selected = selected.sample(n=target_count, random_state=42)

    logger.info(f"Filtered WDPA to {len(selected)} candidate sites")
    return selected

# ----------------------------------------------------------------------
# Main orchestrator
# ----------------------------------------------------------------------
def main() -> None:
    """
    Main entry point for T003 – fetches the WDPA release, extracts the CSV,
    filters for candidate sites, and writes ``site_metadata.csv`` to the
    processed data folder.

    Side‑effects
    ------------
    - ``data/raw/query_log.json`` is appended with the request metadata.
    - ``data/raw/fetch_error.log`` contains error details if anything fails.
    - ``data/processed/site_metadata.csv`` is created with the required
      columns.
    """
    # Ensure required directories exist
    ensure_directories()

    raw_dir = paths.data("raw")
    processed_dir = paths.data("processed")
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    try:
        zip_path = download_wdpa_release(raw_dir)
        wdpa_df = extract_and_load_wdpa(zip_path)
        site_df = filter_and_sample_sites(wdpa_df, target_count=30)

        output_path = processed_dir / "site_metadata.csv"
        site_df.to_csv(output_path, index=False)
        logger.info(f"Site metadata written to {output_path}")

    except Exception as exc:
        # All errors are already logged to fetch_error.log inside helper
        # functions; re‑raise to make the pipeline fail loudly.
        raise RuntimeError(f"T003 failed: {exc}") from exc

if __name__ == "__main__":
    main()
