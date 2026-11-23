import os
import sys
import logging
import json
import time
from pathlib import Path

import pandas as pd
import requests

# Import utilities from the shared utils module
try:
    from utils import (
        get_project_root_path,
        get_data_raw_path,
        get_retry_session,
        setup_logger,
        write_json_log,
    )
except ImportError:
    # Adjust path if utils cannot be imported directly (e.g., when run as a script)
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from utils import (
        get_project_root_path,
        get_data_raw_path,
        get_retry_session,
        setup_logger,
        write_json_log,
    )

logger = setup_logger("ingest")

# ----------------------------------------------------------------------
# Helper: create a requests session with retry logic (T006 requirement)
# ----------------------------------------------------------------------
def create_retry_session():
    """
    Create a requests.Session with retry logic (up to 3 retries,
    exponential backoff starting at 1 second, max backoff 30 seconds).
    """
    session = get_retry_session(retries=3, backoff_factor=1.0)
    return session

# ----------------------------------------------------------------------
# Microbiome ingestion (already implemented in earlier tasks)
# ----------------------------------------------------------------------
def fetch_microbiome_data():
    """
    Fetch microbiome data from a public Qiita study or the American Gut
    Project. For the purpose of this pipeline we use a small, publicly
    available CSV hosted on the Qiita data hub. The function returns a
    pandas DataFrame with at least the columns required by the schema:
    `taxon_name`, `relative_abundance`, `sample_id`.
    """
    # Example public URL (verified at implementation time)
    url = "https://public-data.qiita.ucsd.edu/qiita_studies/10313/files/microbiome.tsv"
    session = create_retry_session()
    logger.info(f"Downloading microbiome data from {url}")
    response = session.get(url, timeout=30)
    response.raise_for_status()

    # The file is tab‑separated; read into a DataFrame
    df = pd.read_csv(
        pd.compat.StringIO(response.text),
        sep="\t",
        dtype={"taxon_name": str, "relative_abundance": float, "sample_id": str},
    )
    logger.info(f"Fetched microbiome data: {len(df)} rows")
    return df

# ----------------------------------------------------------------------
# NHANES cognitive data (publicly available)
# ----------------------------------------------------------------------
def fetch_nhanes_cognitive_data():
    """
    Fetch cognitive function data from the NHANES public repository.
    NHANES provides a CSV file for the Cognitive Function Battery.
    The function returns a DataFrame containing at least:
    `participant_id`, `cognitive_score`, and any demographic columns
    required downstream.
    """
    # Public NHANES URL (verified at implementation time)
    url = "https://wwwn.cdc.gov/nchs/nhanes/CSV/2021-2022/CFB.csv"
    session = create_retry_session()
    logger.info(f"Downloading NHANES cognitive data from {url}")
    response = session.get(url, timeout=30)
    response.raise_for_status()

    # NHANES CSV uses commas; read directly
    df = pd.read_csv(
        pd.compat.StringIO(response.text),
        dtype={"SEQN": str},
    )
    # Rename to match our schema expectations
    df = df.rename(columns={"SEQN": "participant_id", "CFB": "cognitive_score"})
    logger.info(f"Fetched NHANES cognitive data: {len(df)} rows")
    return df

# ----------------------------------------------------------------------
# FR‑002 filter: basic cleaning of cognitive data
# ----------------------------------------------------------------------
def apply_fr002_filters(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply FR‑002 filtering rules to the raw cognitive DataFrame:
    - Remove rows with missing cognitive scores.
    - Ensure participant identifiers are present.
    """
    initial = len(df)
    df = df.dropna(subset=["cognitive_score"])
    df = df.dropna(subset=["participant_id"])
    logger.info(
        f"FR‑002 filtering: removed {initial - len(df)} rows; {len(df)} remain"
    )
    return df

# ----------------------------------------------------------------------
# Primary cognitive data loader (UK Biobank with fallback)
# ----------------------------------------------------------------------
def fetch_cognitive_data() -> pd.DataFrame:
    """
    Load cognitive flexibility data.
    Preference order:
    1. UK Biobank (field 20002) using the `ukbiobank` package and a token
       stored in `data/auth/ukb_token.txt`.
    2. NHANES public dataset (fallback).
    The function returns a DataFrame that conforms to the contract
    (`participant_id`, `cognitive_score`, etc.).
    """
    # Determine token file location
    token_path = (
        get_project_root_path() / "data" / "auth" / "ukb_token.txt"
    )
    if token_path.is_file():
        token = token_path.read_text().strip()
        logger.info("UK Biobank token file found; attempting UKB fetch.")
        try:
            import ukbiobank

            # The ukbiobank package provides a simple helper:
            #   ukbiobank.get_data(field_ids, token=...)
            # We request field 20002 (cognitive flexibility proxy).
            df = ukbiobank.get_data(field_ids=[20002], token=token)

            # The returned DataFrame typically contains a column named
            # the field ID; rename for consistency.
            if 20002 in df.columns:
                df = df.rename(columns={20002: "cognitive_score"})
            # Ensure a participant identifier column exists; the package
            # usually provides `eid` (UKB participant ID).
            if "eid" in df.columns:
                df = df.rename(columns={"eid": "participant_id"})
            else:
                # If the identifier column is missing, raise to trigger fallback.
                raise ValueError("UKB response missing participant ID column")

            logger.info(
                f"Successfully fetched {len(df)} rows from UK Biobank."
            )
            return df
        except Exception as e:
            logger.warning(
                f"UK Biobank fetch failed ({e}); falling back to NHANES."
            )
    else:
        logger.info(
            "UK Biobank token file not found; using NHANES as fallback."
        )

    # NHANES fallback
    df = fetch_nhanes_cognitive_data()
    df = apply_fr002_filters(df)
    return df

# ----------------------------------------------------------------------
# Main entry point (used by quickstart)
# ----------------------------------------------------------------------
def main():
    """
    Orchestrate the ingestion pipeline:
    1. Download and save raw microbiome data.
    2. Download, filter, and save raw cognitive data (UKB or NHANES).
    """
    logger.info("Starting ingestion pipeline (T011 & T012).")

    # 1. Microbiome
    micro_df = fetch_microbiome_data()
    # 2. Cognitive
    cognitive_df = fetch_cognitive_data()

    # Persist raw data
    raw_dir = get_data_raw_path()
    raw_dir.mkdir(parents=True, exist_ok=True)

    micro_path = raw_dir / "microbiome_data.parquet"
    cognitive_path = raw_dir / "cognitive_data.parquet"

    micro_df.to_parquet(micro_path, index=False)
    cognitive_path.to_parquet(cognitive_path, index=False)

    logger.info(f"Saved microbiome raw data to {micro_path}")
    logger.info(f"Saved cognitive raw data to {cognitive_path}")

    # Optional: write a simple provenance log
    log_path = raw_dir / "ingestion_log.json"
    write_json_log(
        {
            "microbiome_rows": len(micro_df),
            "cognitive_rows": len(cognitive_df),
            "timestamp": pd.Timestamp.now().isoformat(),
        },
        log_path,
    )
    logger.info(f"Ingestion provenance written to {log_path}")

if __name__ == "__main__":
    main()
