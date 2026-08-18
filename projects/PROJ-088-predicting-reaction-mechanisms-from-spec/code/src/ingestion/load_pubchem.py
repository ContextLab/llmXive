"""
PubChem Data Loader for Reaction Mechanisms.

Fetches NMR chemical shift data from PubChem, parses provenance fields,
and strictly filters for kinetic studies or validated intermediates.
NO synthetic fallbacks are permitted.
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

if __name__ == "__main__":
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.provenance_filter import should_exclude_row
from src.utils.logging import log_warning, log_error, log_info
from src.utils.io import ensure_directory_exists

# PubChem does not offer a direct "kinetic studies" bulk download via a simple URL
# without specific query construction. We assume a pre-downloaded Parquet file
# or a specific API endpoint for this task.
# To satisfy "Real Data Only", we require a valid source.

DATA_SOURCE_URL = os.getenv("PUBCHEM_NMR_DATA_URL", None)
LOCAL_CACHE = Path("data/raw/pubchem_nmr.parquet")

def load_pubchem_data(output_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Loads PubChem NMR data, strictly filtering by provenance.
    
    Args:
        output_path: Optional path to save the filtered dataframe.
        
    Returns:
        pd.DataFrame: Filtered dataset.
        
    Raises:
        RuntimeError: If data source is unreachable or invalid.
    """
    log_info("Starting PubChem data load with strict provenance filtering.")
    
    source = None
    if DATA_SOURCE_URL:
        source = DATA_SOURCE_URL
    elif LOCAL_CACHE.exists():
        log_info(f"Using local cache: {LOCAL_CACHE}")
        source = str(LOCAL_CACHE)
    else:
        raise RuntimeError(
            "No real data source URL provided and local cache missing. "
            "Set PUBCHEM_NMR_DATA_URL or download data to data/raw/pubchem_nmr.parquet. "
            "Silent fallback to synthetic data is forbidden."
        )

    df = None
    try:
        if isinstance(source, str) and source.endswith(".parquet"):
            if source.startswith("http"):
                # Attempt to download
                import requests
                log_info(f"Downloading {source}")
                resp = requests.get(source, timeout=120)
                resp.raise_for_status()
                df = pd.read_parquet(pd.io.common.BytesIO(resp.content))
            else:
                df = pd.read_parquet(source)
        elif isinstance(source, str) and source.endswith(".csv"):
            if source.startswith("http"):
                import requests
                log_info(f"Downloading {source}")
                resp = requests.get(source, timeout=120)
                resp.raise_for_status()
                df = pd.read_csv(pd.io.common.BytesIO(resp.content))
            else:
                df = pd.read_csv(source)
        else:
            raise ValueError(f"Unsupported source format: {source}")
            
    except Exception as e:
        log_error(f"Failed to fetch or parse PubChem data: {e}")
        raise RuntimeError(f"Real data fetch failed: {e}") from e

    if df is None or df.empty:
        raise RuntimeError("No records found in the real data source.")

    # Check for provenance column
    if 'provenance' not in df.columns:
        log_error("Missing 'provenance' column in PubChem data.")
        # If the real source doesn't have it, we must fail or assume invalid
        raise ValueError("Data source missing required 'provenance' field.")

    # Apply strict provenance filtering
    rows_to_exclude = df.apply(should_exclude_row, axis=1)
    excluded_count = rows_to_exclude.sum()
    included_count = len(df) - excluded_count
    
    log_info(f"Excluded {excluded_count} rows based on provenance. Retained {included_count} rows.")
    
    filtered_df = df[~rows_to_exclude].copy()
    
    if output_path:
        ensure_directory_exists(output_path)
        if output_path.suffix == '.parquet':
            filtered_df.to_parquet(output_path, index=False)
        else:
            filtered_df.to_csv(output_path, index=False)
        log_info(f"Saved filtered data to {output_path}")

    return filtered_df

def main():
    """Main entry point for script execution."""
    output_file = Path("data/processed/pubchem_nmr_filtered.csv")
    try:
        df = load_pubchem_data(output_file)
        log_info(f"Successfully loaded {len(df)} records.")
    except RuntimeError as e:
        log_error(str(e))
        sys.exit(1)
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
