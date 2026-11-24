"""
Data ingestion module for MPEA database processing.
Handles downloading, filtering, and normalizing alloy data.
"""
import os
import sys
import logging
import requests
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import hashlib
import io

# Import shared utilities and config
from utils import (
    setup_logger,
    get_logger,
    compute_sha256,
    verify_sha256,
    PipelineError,
    DataIntegrityError,
    DataScarcityError,
    ensure_directory
)
from env_config import (
    get_raw_data_path,
    get_processed_data_path,
    get_logs_path,
    ensure_dirs
)
from models import AlloyRecord

# Configure logging
logger = setup_logger("data_ingestion")

# Constants
MPEA_DOI = "10.1038/s41597-020-00768-9"
DOI_RESOLVER_URL = f"https://doi.org/{MPEA_DOI}"

def download_mpea_database(output_path: Path) -> Path:
    """
    Downloads the MPEA database using the canonical DOI resolver.

    Args:
        output_path: Path where the downloaded file should be saved.

    Returns:
        Path to the saved file.

    Raises:
        PipelineError: If the DOI resolver fails or returns an empty dataset.
        DataIntegrityError: If the checksum verification fails.
    """
    ensure_directory(output_path.parent)

    logger.info(f"Attempting to resolve DOI: {DOI_RESOLVER_URL}")

    try:
        response = requests.get(DOI_RESOLVER_URL, allow_redirects=True, timeout=30)
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', '')

        if 'text/html' in content_type:
            logger.error("DOI resolver returned an HTML landing page; cannot download data directly.")
            raise PipelineError(
                f"DOI resolver returned a landing page (HTML) instead of a data file. "
                f"Manual intervention required to extract the direct link for {MPEA_DOI}."
            )

        # Write the binary content to the output file
        with open(output_path, 'wb') as f:
            f.write(response.content)

        logger.info(f"Downloaded data to {output_path}")

        if output_path.stat().st_size == 0:
            raise DataIntegrityError(f"Downloaded file {output_path} is empty.")

        return output_path

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download data from DOI resolver: {e}")
        raise PipelineError(
            f"Failed to download MPEA database from DOI resolver ({DOI_RESOLVER_URL}). "
            f"Network error or DOI invalid. Error: {str(e)}"
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        raise PipelineError(
            f"Unexpected error during MPEA database download. Error: {str(e)}"
        ) from e

def load_raw_data(file_path: Path) -> pd.DataFrame:
    """
    Loads the raw data from the downloaded file.

    Args:
        file_path: Path to the downloaded file.

    Returns:
        DataFrame containing the raw data.

    Raises:
        DataIntegrityError: If the file is empty or invalid.
    """
    if not file_path.exists():
        raise DataIntegrityError(f"Raw data file not found: {file_path}")

    if file_path.stat().st_size == 0:
        raise DataIntegrityError(f"Raw data file is empty: {file_path}")

    try:
        if file_path.suffix.lower() == '.xlsx':
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)

        if df.empty:
            raise DataIntegrityError(f"Loaded dataset from {file_path} is empty.")

        logger.info(f"Loaded {len(df)} records from {file_path}")
        return df

    except Exception as e:
        raise DataIntegrityError(f"Failed to parse raw data from {file_path}: {e}") from e

def is_valid_yield_strength(value: Any) -> bool:
    """Checks if the yield strength value is valid (numeric and non-null)."""
    if pd.isna(value):
        return False
    try:
        val = float(value)
        return val > 0
    except (ValueError, TypeError):
        return False

def is_bcc_phase(crystal_structure: Any) -> bool:
    """Checks if the crystal structure is BCC."""
    if pd.isna(crystal_structure):
        return False
    return str(crystal_structure).strip().upper() == 'BCC'

def normalize_composition(composition_dict: Dict[str, float]) -> Dict[str, float]:
    """
    Normalizes a composition dictionary so that the sum of atomic fractions is 1.0.

    Args:
        composition_dict: Dictionary of element: fraction.

    Returns:
        Normalized dictionary.

    Raises:
        PipelineError: If the sum is 0 or negative.
    """
    total = sum(composition_dict.values())
    if total <= 0:
        raise PipelineError(f"Invalid composition sum: {total}. Cannot normalize.")
    return {k: v / total for k, v in composition_dict.items()}

def process_alloy(row: Dict[str, Any]) -> Optional[AlloyRecord]:
    """
    Processes a single alloy row into an AlloyRecord.
    Filters out invalid entries.
    """
    if not is_valid_yield_strength(row.get('yield_strength')):
        return None

    if not is_bcc_phase(row.get('crystal_structure')):
        return None

    comp_str = row.get('composition', '')
    if not isinstance(comp_str, str) or not comp_str:
        return None

    try:
        parts = comp_str.split(',')
        comp = {}
        for part in parts:
            elem, val = part.split(':')
            comp[elem.strip()] = float(val.strip())

        normalized_comp = normalize_composition(comp)

        return AlloyRecord(
            composition=normalized_comp,
            yield_strength=float(row['yield_strength']),
            crystal_structure='BCC',
            source_row=row
        )
    except Exception as e:
        logger.warning(f"Failed to parse composition for row: {e}")
        return None

def filter_bcc_and_yield_strength(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    Filters the dataframe for BCC phase and valid yield strength.

    Returns:
        Tuple of (filtered_df, rejected_entries)
    """
    rejected = []
    valid_rows = []

    for idx, row in df.iterrows():
        if not is_valid_yield_strength(row.get('yield_strength')):
            rejected.append({'index': idx, 'reason': 'Invalid Yield Strength', 'data': row.to_dict()})
            continue
        if not is_bcc_phase(row.get('crystal_structure')):
            rejected.append({'index': idx, 'reason': 'Non-BCC Phase', 'data': row.to_dict()})
            continue
        valid_rows.append(row.to_dict())

    if len(valid_rows) == 0:
        raise DataScarcityError("DATA_SCARCITY: No valid BCC alloys with yield strength found.")

    filtered_df = pd.DataFrame(valid_rows)
    return filtered_df, rejected

def check_data_scarcity(df: pd.DataFrame, min_count: int = 80) -> None:
    """
    Checks if the dataset has enough samples.

    Raises:
        DataScarcityError: If count is below threshold.
    """
    count = len(df)
    if count < min_count:
        raise DataScarcityError(f"DATA_SCARCITY: Insufficient BCC alloys (N={count} < {min_count})")
    logger.info(f"Data scarcity check passed: N={count} >= {min_count}")

def save_filtered_output(df: pd.DataFrame, rejected: List[Dict], output_path: Path, log_path: Path) -> None:
    """
    Saves the filtered dataframe and rejected entries.
    """
    ensure_directory(output_path.parent)
    ensure_directory(log_path.parent)

    df.to_csv(output_path, index=False)
    logger.info(f"Saved filtered data to {output_path}")

    with open(log_path, 'w') as f:
        for entry in rejected:
            f.write(f"Index: {entry['index']}, Reason: {entry['reason']}\n")
            f.write(f"Data: {entry['data']}\n")
            f.write("---\n")
    logger.info(f"Saved rejected entries to {log_path}")

def main():
    """Main entry point for data ingestion."""
    ensure_dirs()

    # NOTE: The original script used an .xlsx filename; for compatibility with the
    # quickstart expectations we store the raw download as a CSV.
    raw_path = get_raw_data_path() / "mpea_raw.csv"
    processed_path = get_processed_data_path() / "bcc_filtered.csv"
    log_path = get_logs_path() / "rejected_entries.log"

    try:
        logger.info("Starting download...")
        download_mpea_database(raw_path)

        logger.info("Loading raw data...")
        df = load_raw_data(raw_path)

        logger.info("Filtering BCC and yield strength...")
        filtered_df, rejected = filter_bcc_and_yield_strength(df)

        logger.info("Checking data scarcity...")
        check_data_scarcity(filtered_df)

        logger.info("Saving results...")
        save_filtered_output(filtered_df, rejected, processed_path, log_path)

        logger.info("Data ingestion completed successfully.")
    except (PipelineError, DataIntegrityError, DataScarcityError) as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
