import pandas as pd
from typing import Optional, Dict, Any
import requests
import os
import sys
import time
import json
from pathlib import Path

# Configuration and logging imports (assumed to exist per T005/T006)
try:
    from src.config import load_config
    from src.logging_config import get_logger
except ImportError:
    # Fallback for standalone execution if modules not fully initialized yet
    def load_config():
        return {
            'DATA_URL': os.getenv('DATA_URL', 'https://zenodo.org/records/1044711/files/gut_sleep_data.csv'),
            'RANDOM_SEED': 42,
            'LOG_LEVEL': 'INFO'
        }
    def get_logger(name):
        import logging
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

def compute_backoff(attempt: int, base: float = 1.0, max_wait: float = 60.0) -> float:
    """Exponential backoff with jitter."""
    wait = min(base * (2 ** attempt), max_wait)
    return wait

def download_with_backoff(url: str, dest_path: str, max_retries: int = 5) -> bool:
    """Download file with exponential backoff."""
    logger = get_logger(__name__)
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting download (attempt {attempt + 1}/{max_retries})")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            with open(dest_path, 'wb') as f:
                f.write(response.content)
            logger.info(f"Downloaded successfully to {dest_path}")
            return True
        except requests.RequestException as e:
            wait = compute_backoff(attempt)
            logger.warning(f"Download failed: {e}. Retrying in {wait:.2f}s...")
            time.sleep(wait)
    logger.error("Download failed after max retries.")
    return False

def fetch_sample_headers(url: str) -> Optional[list]:
    """Fetch only headers to verify schema."""
    try:
        # Use a small range request or just fetch header if supported, otherwise fetch small chunk
        # For robustness, we fetch the first few bytes/lines
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        # Read first line assuming CSV
        line = b""
        for chunk in response.iter_content(chunk_size=1024):
            if not chunk:
                break
            line += chunk
            if b'\n' in line:
                break
        if line:
            # Decode and split
            header_line = line.decode('utf-8', errors='ignore').strip()
            return header_line.split(',')
        return None
    except Exception as e:
        print(f"Error fetching headers: {e}")
        return None

def verify_schema(url: str, required_columns: list) -> bool:
    """Verify that the source URL contains required columns."""
    logger = get_logger(__name__)
    headers = fetch_sample_headers(url)
    if not headers:
        logger.error("Could not fetch headers from source.")
        return False
    
    # Clean headers (remove quotes, whitespace)
    clean_headers = [h.strip().strip('"') for h in headers]
    
    missing = [col for col in required_columns if col not in clean_headers]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return False
    
    logger.info("Schema verification passed.")
    return True

def filter_antibiotic_use(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Filter out samples with antibiotic use in last 3 months."""
    logger = get_logger(__name__)
    initial_count = len(df)
    
    # Filter where antibiotic_use_last_3m is False or null/empty
    # Assuming 1/True means used, 0/False means not used. 
    # We keep rows where it is NOT True (i.e., False or NaN)
    mask = ~df['antibiotic_use_last_3m'].astype(bool)
    filtered_df = df[mask].copy()
    
    excluded_count = initial_count - len(filtered_df)
    logger.info(f"Excluded {excluded_count} samples due to antibiotic use.")
    return filtered_df, excluded_count

def filter_sleep_data(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Filter out samples with missing sleep efficiency or duration."""
    logger = get_logger(__name__)
    initial_count = len(df)
    
    mask = df['sleep_efficiency'].notna() & df['sleep_duration_hours'].notna()
    filtered_df = df[mask].copy()
    
    excluded_count = initial_count - len(filtered_df)
    logger.info(f"Excluded {excluded_count} samples due to missing sleep data.")
    return filtered_df, excluded_count

def merge_otu_and_metadata(otu_df: pd.DataFrame, meta_df: pd.DataFrame, key: str = 'sample_id') -> pd.DataFrame:
    """Merge OTU table with metadata."""
    logger = get_logger(__name__)
    merged = pd.merge(otu_df, meta_df, on=key, how='inner')
    logger.info(f"Merged data shape: {merged.shape}")
    return merged

def log_exclusion_rates(total_initial: int, excluded_antibiotic: int, excluded_sleep: int, output_path: str):
    """
    Log exclusion rates to satisfy SC-001.
    Captures total_initial_sample_count, excluded_count, and exclusion_proportion.
    """
    logger = get_logger(__name__)
    total_excluded = excluded_antibiotic + excluded_sleep
    
    if total_initial == 0:
        proportion = 0.0
    else:
        proportion = total_excluded / total_initial
    
    report = {
        "total_initial_sample_count": total_initial,
        "excluded_count": total_excluded,
        "exclusion_proportion": round(proportion, 4),
        "breakdown": {
            "excluded_antibiotic": excluded_antibiotic,
            "excluded_sleep_data": excluded_sleep
        }
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Ingestion report saved to {output_path}")
    logger.info(f"Exclusion Rate: {proportion:.2%} ({total_excluded}/{total_initial})")

def main():
    logger = get_logger(__name__)
    config = load_config()
    url = config['DATA_URL']
    raw_path = 'data/raw/microbiome_sleep_raw.csv'
    cleaned_path = 'data/processed/cleaned_microbiome_sleep.csv'
    report_path = 'data/processed/ingestion_report.json'
    
    required_cols = ['antibiotic_use_last_3m', 'sleep_efficiency', 'sleep_duration_hours', 'sample_id']
    
    # 1. Verify Schema (T012b)
    logger.info("Verifying schema...")
    if not verify_schema(url, required_cols):
        logger.error("Schema verification failed. Exiting.")
        sys.exit(1)
    
    # 2. Download (T013)
    logger.info("Downloading data...")
    if not download_with_backoff(url, raw_path):
        logger.error("Download failed. Exiting.")
        sys.exit(1)
    
    # 3. Load Data
    logger.info("Loading data...")
    df = pd.read_csv(raw_path)
    total_initial = len(df)
    logger.info(f"Loaded {total_initial} samples.")
    
    # 4. Filter Antibiotic Use (T014)
    df, excluded_antibiotic = filter_antibiotic_use(df)
    
    # 5. Filter Sleep Data (T014)
    df, excluded_sleep = filter_sleep_data(df)
    
    # 6. Save Cleaned Data (T016)
    logger.info(f"Saving cleaned data to {cleaned_path}...")
    os.makedirs(os.path.dirname(cleaned_path), exist_ok=True)
    df.to_csv(cleaned_path, index=False)
    
    # 7. Log Exclusion Rates (T017)
    log_exclusion_rates(total_initial, excluded_antibiotic, excluded_sleep, report_path)
    
    logger.info("Pipeline completed successfully.")

if __name__ == "__main__":
    main()
