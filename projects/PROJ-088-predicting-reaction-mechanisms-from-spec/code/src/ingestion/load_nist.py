"""
NIST WebBook Data Loader for Reaction Mechanisms.

Fetches IR/NMR data from NIST WebBook, parses provenance fields,
and strictly filters for kinetic studies or validated intermediates.
NO synthetic fallbacks are permitted.
"""
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import requests

# Add project root to path for imports if running as script
if __name__ == "__main__":
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.provenance_filter import should_exclude_row
from src.utils.logging import log_warning, log_error, log_info, log_provenance_mismatch

NIST_BASE_URL = "https://webbook.nist.gov/cgi/cbook.cgi"
# Note: NIST WebBook does not have a direct bulk JSONL API for kinetic studies.
# This loader simulates the fetch pattern or fetches from a mirrored dataset
# if a specific endpoint is available. For this implementation, we assume
# a JSONL file is hosted or we iterate a known list of IDs.
# To satisfy "Real Data Only", we will attempt to fetch from a specific
# public mirror or fail loudly if the source is unreachable.

# Using a representative URL for the dataset if a bulk download exists.
# If not, we implement a fetch loop for a known set of kinetic study IDs.
# For this task, we assume a specific JSONL endpoint or file structure.
# Since NIST doesn't expose a raw JSONL "all kinetic studies" endpoint directly
# without scraping, we will implement a robust fetcher that attempts to
# retrieve a known dataset file if available, or fetches specific records.

# Placeholder for a real data source URL. In a real pipeline, this would be
# a specific S3 bucket, Zenodo DOI, or NIST FTP path.
# For the purpose of this task's "Real Data" constraint, we will attempt
# to fetch from a known public dataset if the environment variable is set,
# otherwise we raise an error to prevent silent failure.
DATA_SOURCE_URL = os.getenv("NIST_KINETIC_DATA_URL", None)

def load_nist_data(output_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Loads NIST data, strictly filtering by provenance.
    
    Args:
        output_path: Optional path to save the filtered dataframe.
        
    Returns:
        pd.DataFrame: Filtered dataset with only kinetic/validated rows.
        
    Raises:
        RuntimeError: If data source is unreachable or no valid data is found.
    """
    log_info("Starting NIST data load with strict provenance filtering.")
    
    # Check for real data source
    if not DATA_SOURCE_URL:
        # In a real execution, this would be a specific URL provided by the pipeline
        # or a pre-downloaded file. We simulate the check.
        # If no URL is provided, we cannot proceed with "Real Data Only".
        # However, to make the code runnable for testing if a file exists locally:
        local_file = Path("data/raw/nist_kinetic.jsonl")
        if local_file.exists():
            log_info(f"Loading from local cache: {local_file}")
            data_source = local_file
        else:
            raise RuntimeError(
                "No real data source URL provided and local cache missing. "
                "Set NIST_KINETIC_DATA_URL or download data to data/raw/nist_kinetic.jsonl. "
                "Silent fallback to synthetic data is forbidden."
            )
    else:
        data_source = DATA_SOURCE_URL

    records = []
    try:
        if isinstance(data_source, str) and data_source.startswith("http"):
            log_info(f"Fetching data from {data_source}")
            response = requests.get(data_source, timeout=60)
            response.raise_for_status()
            lines = response.text.splitlines()
            for line in lines:
                if line.strip():
                    records.append(json.loads(line))
        else:
            # Local file
            with open(data_source, 'r') as f:
                for line in f:
                    if line.strip():
                        records.append(json.loads(line))
                        
    except Exception as e:
        log_error(f"Failed to fetch or parse NIST data: {e}")
        raise RuntimeError(f"Real data fetch failed: {e}") from e

    if not records:
        raise RuntimeError("No records found in the real data source.")

    # Convert to DataFrame
    df = pd.DataFrame(records)
    
    if 'provenance' not in df.columns:
        log_error("Missing 'provenance' column in NIST data.")
        raise ValueError("Data source missing required 'provenance' field.")

    # Apply strict provenance filtering
    # The filter function returns True for rows to EXCLUDE
    rows_to_exclude = df.apply(should_exclude_row, axis=1)
    excluded_count = rows_to_exclude.sum()
    included_count = len(df) - excluded_count
    
    log_info(f"Excluded {excluded_count} rows based on provenance. Retained {included_count} rows.")
    
    if included_count == 0:
        log_warning("No valid kinetic study records found after filtering.")
        # Do not return empty df without warning if real data was expected
        # But we return it to allow downstream checks to fail explicitly
        
    filtered_df = df[~rows_to_exclude].copy()
    
    # Ensure output path is handled if provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        filtered_df.to_csv(output_path, index=False)
        log_info(f"Saved filtered data to {output_path}")

    return filtered_df

def main():
    """Main entry point for script execution."""
    output_file = Path("data/processed/nist_kinetic_filtered.csv")
    try:
        df = load_nist_data(output_file)
        log_info(f"Successfully loaded {len(df)} records.")
        # Verify no NaNs in labels if 'label' column exists
        if 'label' in df.columns:
            nan_count = df['label'].isna().sum()
            if nan_count > 0:
                log_warning(f"Found {nan_count} NaN labels in filtered data.")
    except RuntimeError as e:
        log_error(str(e))
        sys.exit(1)
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
