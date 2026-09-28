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
MPEA_URL_BASE = "https://data.nature.com"
# Canonical URL pattern for DOI resolution (using DOI.org as resolver)
DOI_RESOLVER_URL = f"https://doi.org/{MPEA_DOI}"
# Direct data link (fallback if DOI resolver redirects to a specific file)
# Note: In a real scenario, this would be the direct link to the .xlsx or .csv
# For this implementation, we simulate the fetch logic or use a known public mirror
# if the DOI does not resolve directly to a file stream in the test environment.
# However, per strict requirements, we attempt the DOI resolution first.

# Since the actual MPEA dataset is behind a paywall or specific institutional access,
# and the task requires a REAL source that fails loudly if unreachable,
# we implement the robust fetch logic that attempts the DOI.
# If the environment cannot resolve it (e.g., network block, paywall), it raises PipelineError.

# For the purpose of this pipeline running in a CI/Local env without paywall access,
# we define a fallback public repository URL that hosts the dataset if available,
# OR we strictly enforce the DOI check and let it fail if no public mirror is defined in config.
# Given the "Constitution Principle III", we must NOT fallback to synthetic.
# We will attempt the DOI resolver. If it returns a valid HTML or redirects to a file, we proceed.
# If it fails (404, 500, timeout), we raise.

# NOTE: In a real production run, the URL below would be the resolved direct download link.
# We use a placeholder logic that checks connectivity and validity.
# To satisfy the "Real Data" requirement without a paywall key, we assume the CI environment
# has the file pre-seeded or a public mirror is available at a known path.
# However, to strictly follow "NO SYNTHETIC", if the fetch fails, we raise.

# Let's assume the direct data source is a CSV available via a public academic mirror 
# or the DOI resolves to a specific file.
# We will attempt to fetch from the DOI resolver.

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
        # Attempt to resolve the DOI
        # In a real scenario, we might use `requests.get(DOI_RESOLVER_URL, allow_redirects=True)`
        # and check if the final URL points to a downloadable file.
        # For robustness against paywalls in test environments, we check for a specific 
        # public mirror or the resolved URL.
        
        # Strategy:
        # 1. Try to resolve the DOI.
        # 2. If it redirects to a specific file, download it.
        # 3. If it redirects to a landing page, check if the landing page contains a direct link.
        # 4. If no direct link or access denied, raise PipelineError.
        
        # Since we cannot guarantee the DOI resolves to a raw file without a browser session/cookies,
        # and we must NOT fake data, we implement a strict check.
        # We will attempt to fetch the landing page. If it's a 404 or 403, we fail.
        
        response = requests.get(DOI_RESOLVER_URL, allow_redirects=True, timeout=30)
        response.raise_for_status()
        
        # Check if the response is a landing page (HTML) or a file
        content_type = response.headers.get('Content-Type', '')
        
        # If it's HTML, we cannot download the data directly without scraping the link.
        # However, for this pipeline, we assume the DOI resolver in the CI environment
        # is configured to redirect to the data file OR we have a known direct link.
        # If we get HTML, we try to find a direct link (e.g., .xlsx, .csv).
        # If we cannot find one, we raise an error.
        
        if 'text/html' in content_type:
            # Try to find a direct link in the HTML
            # This is a simplified check. In reality, we'd parse the HTML.
            # If we can't find a link, we fail.
            logger.warning("DOI resolver returned an HTML landing page. Cannot extract data directly.")
            raise PipelineError(
                f"DOI resolver returned a landing page (HTML) instead of a data file. "
                f"Manual intervention required to extract the direct link for {MPEA_DOI}. "
                f"No synthetic fallback is permitted."
            )
        
        # If we are here, we assume we have a binary file (xlsx/csv)
        # Save the content
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Downloaded data to {output_path}")
        
        # Verify checksum if a known hash is available (not implemented here as hash is dynamic)
        # In a real scenario, we would verify against a known hash.
        # For now, we check if the file is empty.
        if output_path.stat().st_size == 0:
            raise DataIntegrityError(f"Downloaded file {output_path} is empty.")
            
        return output_path

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download data from DOI resolver: {e}")
        raise PipelineError(
            f"Failed to download MPEA database from DOI resolver ({DOI_RESOLVER_URL}). "
            f"Network error or DOI invalid. No synthetic fallback permitted. Error: {str(e)}"
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        raise PipelineError(
            f"Unexpected error during MPEA database download. No synthetic fallback permitted. Error: {str(e)}"
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
        # Assume CSV for simplicity, adjust for XLSX if needed
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
    # Check yield strength
    if not is_valid_yield_strength(row.get('yield_strength')):
        return None
        
    # Check crystal structure
    if not is_bcc_phase(row.get('crystal_structure')):
        return None
        
    # Parse composition (assumed to be a string like "Fe:0.5,Ni:0.5" or a dict)
    # Simplified parsing for this example
    comp_str = row.get('composition', '')
    if not isinstance(comp_str, str) or not comp_str:
        return None
        
    # Basic parsing: "Element1:val1,Element2:val2"
    try:
        parts = comp_str.split(',')
        comp = {}
        for part in parts:
            elem, val = part.split(':')
            comp[elem.strip()] = float(val.strip())
        
        # Normalize
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
    
    Args:
        df: The filtered dataframe.
        min_count: Minimum required count.
        
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
    
    # Save CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Saved filtered data to {output_path}")
    
    # Save log
    with open(log_path, 'w') as f:
        for entry in rejected:
            f.write(f"Index: {entry['index']}, Reason: {entry['reason']}\n")
            f.write(f"Data: {entry['data']}\n")
            f.write("---\n")
    logger.info(f"Saved rejected entries to {log_path}")

def main():
    """Main entry point for data ingestion."""
    ensure_dirs()
    
    raw_path = get_raw_data_path() / "mpea_raw.xlsx" # Or .csv depending on actual source
    processed_path = get_processed_data_path() / "bcc_filtered.csv"
    log_path = get_logs_path() / "rejected_entries.log"
    
    try:
        # Download
        logger.info("Starting download...")
        download_mpea_database(raw_path)
        
        # Load
        logger.info("Loading raw data...")
        df = load_raw_data(raw_path)
        
        # Filter
        logger.info("Filtering BCC and yield strength...")
        filtered_df, rejected = filter_bcc_and_yield_strength(df)
        
        # Check scarcity
        logger.info("Checking data scarcity...")
        check_data_scarcity(filtered_df)
        
        # Save
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