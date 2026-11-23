import pandas as pd
from typing import Optional, Dict, Any, Generator, Iterable
import requests
import os
import sys
import time
import logging
from pathlib import Path

# Import config to get DATA_URL and paths
from src.config import load_config

# Setup logging
logger = logging.getLogger(__name__)

def compute_backoff(attempt: int, base: float = 1.0, max_wait: float = 60.0) -> float:
    """Exponential backoff with jitter."""
    wait = min(base * (2 ** attempt), max_wait)
    return wait + (time.time() % 1)  # Simple jitter

def download_with_backoff(url: str, output_path: str, max_retries: int = 5) -> bool:
    """Download file with exponential backoff."""
    for attempt in range(max_retries):
        try:
            logger.info(f"Downloading from {url} (attempt {attempt + 1})")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Downloaded successfully to {output_path}")
            return True
        except requests.RequestException as e:
            wait = compute_backoff(attempt)
            logger.warning(f"Download failed: {e}. Retrying in {wait:.2f}s...")
            time.sleep(wait)
    
    logger.error(f"Failed to download after {max_retries} attempts")
    return False

def fetch_sample_headers(url: str) -> Optional[list]:
    """Fetch headers of the CSV to verify structure."""
    try:
        # Use a small chunk to get headers
        response = requests.get(url, stream=True)
        response.raise_for_status()
        # Read first line for headers
        first_line = next(iter(response.iter_lines(decode_unicode=True)))
        return first_line.split(',')
    except Exception as e:
        logger.error(f"Failed to fetch headers: {e}")
        return None

def verify_schema(headers: list, required_columns: list) -> bool:
    """Verify that required columns exist in headers."""
    if not headers:
        return False
    header_set = set(col.strip().lower() for col in headers)
    required_set = set(col.strip().lower() for col in required_columns)
    return required_set.issubset(header_set)

def filter_antibiotic_use(df: pd.DataFrame, column: str = 'antibiotic_use_last_3m') -> pd.DataFrame:
    """
    Filter out samples where antibiotic_use_last_3m is True.
    Keeps rows where the column is False, NaN, or explicitly 'False'/'false'/'no'/'n'.
    """
    if column not in df.columns:
        logger.warning(f"Column '{column}' not found. Skipping antibiotic filter.")
        return df

    # Convert column to string to handle mixed types, then normalize
    # We want to EXCLUDE True, 'True', 'yes', 'y', '1'
    # We want to KEEP False, 'False', 'no', 'n', '0', NaN, None
    
    def is_antibiotic_user(val):
        if pd.isna(val):
            return False  # Keep missing (treat as no antibiotic)
        val_str = str(val).lower().strip()
        return val_str in ['true', 'yes', 'y', '1']

    mask = ~df[column].apply(is_antibiotic_user)
    return df[mask]

def filter_sleep_data(df: pd.DataFrame, 
                      sleep_efficiency_col: str = 'sleep_efficiency', 
                      sleep_duration_col: str = 'sleep_duration_hours') -> pd.DataFrame:
    """
    Filter out samples where sleep_efficiency or sleep_duration_hours are null/missing.
    """
    if sleep_efficiency_col not in df.columns or sleep_duration_col not in df.columns:
        logger.warning(f"Sleep columns not found. Skipping sleep data filter.")
        return df

    # Keep rows where BOTH columns are not null
    mask = df[sleep_efficiency_col].notna() & df[sleep_duration_col].notna()
    return df[mask]

def merge_otu_and_metadata(otu_df: pd.DataFrame, metadata_df: pd.DataFrame, key: str = 'sample_id') -> pd.DataFrame:
    """Merge OTU table with metadata on sample_id."""
    if key not in otu_df.columns or key not in metadata_df.columns:
        raise ValueError(f"Merge key '{key}' not found in both dataframes.")
    
    return pd.merge(otu_df, metadata_df, on=key, how='inner')

def log_exclusion_rates(initial_count: int, final_count: int, output_path: str) -> Dict[str, Any]:
    """
    Log exclusion rates to a JSON report file.
    Returns the report dictionary.
    """
    excluded_count = initial_count - final_count
    exclusion_proportion = excluded_count / initial_count if initial_count > 0 else 0.0
    
    report = {
        "status": "success",
        "total_initial_sample_count": initial_count,
        "excluded_count": excluded_count,
        "exclusion_proportion": exclusion_proportion,
        "remaining_count": final_count
    }
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    import json
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Exclusion rates logged: {excluded_count} excluded ({exclusion_proportion:.2%})")
    return report

def run_ingestion_pipeline(
    data_url: Optional[str] = None,
    output_path: str = 'data/processed/cleaned_microbiome_sleep.csv',
    report_path: str = 'data/processed/ingestion_report.json'
) -> Dict[str, Any]:
    """
    Main pipeline: Download, Filter (Antibiotic + Sleep), and Save.
    This function implements T014 (Filtering) and part of T016/T017 (Save/Log).
    """
    config = load_config()
    url = data_url or config.get('DATA_URL')
    
    if not url:
        raise ValueError("No DATA_URL provided or found in config.")
    
    # Temporary file for download
    temp_path = 'data/raw/temp_download.csv'
    Path(temp_path).parent.mkdir(parents=True, exist_ok=True)
    
    # 1. Download (T013 logic, assumed to be called here or pre-run)
    # For T014, we assume the file is available or download it here if needed
    if not os.path.exists(temp_path):
        if not download_with_backoff(url, temp_path):
            raise RuntimeError("Data download failed.")
    
    # 2. Load Data
    logger.info("Loading data...")
    try:
        # Try chunked loading if file is huge, but for filtering we need to read sequentially
        # If memory is a concern, we could iterate, but pandas is efficient enough for typical sizes
        df = pd.read_csv(temp_path)
    except Exception as e:
        logger.error(f"Failed to load CSV: {e}")
        raise

    initial_count = len(df)
    logger.info(f"Initial sample count: {initial_count}")

    # 3. Filter Antibiotic Users (T014 Core)
    logger.info("Filtering antibiotic users...")
    df_filtered = filter_antibiotic_use(df, 'antibiotic_use_last_3m')
    after_antibiotic_count = len(df_filtered)
    logger.info(f"After antibiotic filter: {after_antibiotic_count} samples")

    # 4. Filter Missing Sleep Data (T014 Core)
    logger.info("Filtering missing sleep data...")
    df_clean = filter_sleep_data(df_filtered, 'sleep_efficiency', 'sleep_duration_hours')
    final_count = len(df_clean)
    logger.info(f"After sleep filter: {final_count} samples")

    # 5. Save Cleaned Data (T016)
    logger.info(f"Saving cleaned data to {output_path}...")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(output_path, index=False)
    
    # 6. Log Exclusion Rates (T017)
    report = log_exclusion_rates(initial_count, final_count, report_path)
    
    # Cleanup temp file
    if os.path.exists(temp_path):
        os.remove(temp_path)
        logger.info("Cleaned up temporary file.")

    return report

def main():
    """Entry point for script execution."""
    logging.basicConfig(level=logging.INFO)
    try:
        result = run_ingestion_pipeline()
        print(f"Pipeline completed successfully. Report: {result}")
    except Exception as e:
        logging.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
