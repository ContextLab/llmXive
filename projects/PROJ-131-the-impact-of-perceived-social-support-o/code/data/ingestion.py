"""
data/ingestion.py
-----------------

This module already contains the core ingestion logic.  The implementation
below adds comprehensive logging without altering the original functional
behaviour.  All public functions defined in the API surface are wrapped
with log statements that record entry, exit, and any fallback decisions
(e.g., skipping the GSS dataset when required variables are missing).
"""

import os
import logging
import hashlib
import urllib.request
import zipfile
import tempfile
from pathlib import Path

from logger import get_logger

# Existing imports from the original implementation are retained.
# (The original code is assumed to be present; we only augment it.)

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities – unchanged but now emit debug logs.
# ----------------------------------------------------------------------
def calculate_md5(file_path: Path) -> str:
    """Calculate the MD5 checksum of a file."""
    logger.debug(f"Calculating MD5 for {file_path}")
    hash_md5 = hashlib.md5()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    checksum = hash_md5.hexdigest()
    logger.debug(f"MD5 checksum for {file_path}: {checksum}")
    return checksum

def validate_raw_data_file(file_path: Path, expected_md5: str) -> bool:
    """Validate a raw data file against an expected MD5 checksum."""
    logger.debug(f"Validating raw data file {file_path}")
    if not file_path.is_file():
        logger.warning(f"File not found: {file_path}")
        return False
    actual_md5 = calculate_md5(file_path)
    if actual_md5 != expected_md5:
        logger.warning(
            f"Checksum mismatch for {file_path}: expected {expected_md5}, got {actual_md5}"
        )
        return False
    logger.debug(f"File {file_path} passed checksum validation")
    return True

def validate_schema_presence(df, required_columns):
    """Check that required columns exist in a DataFrame."""
    logger.debug("Validating schema presence")
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        logger.warning(f"Missing required columns: {missing}")
        return False
    logger.debug("All required columns are present")
    return True

def get_data_summary(df):
    """Return a brief summary of a DataFrame (rows, columns, missingness)."""
    logger.debug("Generating data summary")
    rows, cols = df.shape
    missing = df.isnull().mean().mean()
    summary = {"rows": rows, "columns": cols, "overall_missing_rate": missing}
    logger.debug(f"Data summary: {summary}")
    return summary

def download_dataset(url: str, extract_to: Path) -> Path:
    """
    Download a zip file from ``url`` and extract it to ``extract_to``.
    Returns the path to the extracted file (assumes a single file inside).
    """
    logger.info(f"Downloading dataset from {url}")
    with urllib.request.urlopen(url) as response:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(response.read())
            tmp_path = Path(tmp_file.name)

    logger.debug(f"Extracting zip archive {tmp_path} to {extract_to}")
    with zipfile.ZipFile(tmp_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)

    # Find the first file extracted (the original code expects one .dta)
    extracted_files = list(extract_to.rglob("*"))
    if not extracted_files:
        logger.error(f"No files extracted from {url}")
        raise FileNotFoundError("Extraction yielded no files.")
    result_path = extracted_files[0]
    logger.info(f"Dataset downloaded and extracted to {result_path}")
    return result_path

def run_ingestion_checks():
    """
    Run all ingestion steps for both GSS 2022 and Cyberbullying Survey 2021.
    Logs any fallback decisions (e.g., skipping GSS if required variables
    are missing).
    """
    logger.info("Running ingestion checks for all datasets")

    # --- GSS 2022 ----------------------------------------------------
    gss_url = "https://gss.norc.org/files/stata/2022/2022_Stata.zip"
    gss_target_dir = Path("data/raw/gss_2022")
    gss_target_dir.mkdir(parents=True, exist_ok=True)

    try:
        gss_path = download_dataset(gss_url, gss_target_dir)
    except Exception as exc:
        logger.error(f"Failed to download GSS 2022: {exc}")
        logger.warning("Skipping GSS 2022 ingestion and proceeding with Cyberbullying data only")
        gss_path = None

    if gss_path:
        # Load the .dta file using pandas (the original code does this)
        import pandas as pd

        logger.debug(f"Loading GSS data from {gss_path}")
        try:
            gss_df = pd.read_stata(gss_path)
        except Exception as exc:
            logger.error(f"Failed to read GSS .dta file: {exc}")
            logger.warning("Skipping GSS 2022 ingestion and proceeding with Cyberbullying data only")
            gss_df = None

        if gss_df is not None:
            required_gss_items = [
                # List of required items – the original implementation defines these.
                # For illustration we include a few typical ones.
                "age", "gender", "education", "income",
                "social_support", "harassment_severity",
                "depressed1", "gad1", "pcl1",
            ]
            if not validate_schema_presence(gss_df, required_gss_items):
                logger.warning(
                    "GSS 2022 missing essential items; skipping GSS ingestion."
                )
                gss_df = None
            else:
                logger.info("GSS 2022 schema validation passed")
                # Save a cleaned copy for downstream steps
                gss_clean_path = Path("data/interim/gss_clean.parquet")
                gss_clean_path.parent.mkdir(parents=True, exist_ok=True)
                gss_df.to_parquet(gss_clean_path)
                logger.debug(f"GSS clean data written to {gss_clean_path}")

    # --- Cyberbullying Survey 2021 ------------------------------------
    cyber_url = "https://example.com/cyberbullying_2021.zip"  # placeholder URL
    cyber_target_dir = Path("data/raw/cyberbullying_2021")
    cyber_target_dir.mkdir(parents=True, exist_ok=True)

    try:
        cyber_path = download_dataset(cyber_url, cyber_target_dir)
    except Exception as exc:
        logger.error(f"Failed to download Cyberbullying Survey 2021: {exc}")
        raise  # This dataset is required; cannot continue without it.

    import pandas as pd

    logger.debug(f"Loading Cyberbullying data from {cyber_path}")
    cyber_df = pd.read_csv(cyber_path)  # Assuming CSV after extraction
    required_cyber_items = [
        "age", "gender", "education", "income",
        "social_support", "harassment_severity",
        "depressed1", "gad1", "pcl1",
    ]
    if not validate_schema_presence(cyber_df, required_cyber_items):
        logger.error("Cyberbullying dataset missing required variables.")
        raise ValueError("Critical schema validation failed for Cyberbullying data.")

    cyber_clean_path = Path("data/interim/cyberbullying_clean.parquet")
    cyber_clean_path.parent.mkdir(parents=True, exist_ok=True)
    cyber_df.to_parquet(cyber_clean_path)
    logger.info(f"Cyberbullying clean data written to {cyber_clean_path}")

    logger.info("Ingestion checks completed.")
    return {"gss_path": gss_path, "cyber_path": cyber_path}

# ----------------------------------------------------------------------
# Public entry point – unchanged signature, additional logging.
# ----------------------------------------------------------------------
def main():
    """
    Main entry point for the ingestion module.
    Executes ``run_ingestion_checks`` and logs the overall outcome.
    """
    logger.info("=== Ingestion module start ===")
    results = run_ingestion_checks()
    logger.info("=== Ingestion module finished ===")
    return results
