import pandas as pd
from typing import Optional, Dict, Any
import requests
import os
import sys
import time
import logging
import json
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration constants
DATA_DIR = Path("data/processed")
CLEANED_OUTPUT_PATH = DATA_DIR / "cleaned_microbiome_sleep.csv"
REPORT_PATH = DATA_DIR / "ingestion_report.json"

def compute_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """Exponential backoff with jitter."""
    delay = min(base_delay * (2 ** attempt), max_delay)
    jitter = delay * 0.1
    return delay + jitter

def download_with_backoff(url: str, output_path: Path, max_retries: int = 5) -> None:
    """Download file with exponential backoff."""
    for attempt in range(max_retries):
        try:
            logger.info(f"Downloading {url} (attempt {attempt + 1}/{max_retries})")
            response = requests.get(url, timeout=300)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Successfully downloaded to {output_path}")
            return
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to download after {max_retries} attempts: {e}")
                raise
            delay = compute_backoff(attempt)
            logger.warning(f"Download failed: {e}. Retrying in {delay:.2f}s...")
            time.sleep(delay)

def fetch_sample_headers(url: str) -> list:
    """Fetch headers from the URL without downloading full file."""
    try:
        response = requests.head(url, timeout=30)
        if response.status_code == 200:
            # For CSV, we might need to fetch a small sample
            response = requests.get(url, headers={'Range': 'bytes=0-1024'}, timeout=30)
            lines = response.text.split('\n')
            if lines:
                return lines[0].split(',')
            return []
        else:
            logger.error(f"Failed to fetch headers: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error fetching headers: {e}")
        return []

def verify_schema(headers: list, required_columns: list) -> bool:
    """Verify that required columns exist in the dataset."""
    missing = [col for col in required_columns if col not in headers]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return False
    return True

def filter_antibiotic_use(df: pd.DataFrame) -> pd.DataFrame:
    """Filter out samples with antibiotic use in the last 3 months."""
    initial_count = len(df)
    
    # Filter out rows where antibiotic_use_last_3m is True
    # Assuming True, 'true', 'Yes', 'yes' indicate antibiotic use
    antibiotic_true_values = [True, 'true', 'True', 'TRUE', 'Yes', 'yes', 'YES', 1, '1']
    
    mask = ~df['antibiotic_use_last_3m'].isin(antibiotic_true_values)
    filtered_df = df[mask].copy()
    
    excluded_count = initial_count - len(filtered_df)
    logger.info(f"Antibiotic exclusion: {excluded_count} samples removed ({excluded_count/initial_count*100:.2f}%)")
    
    return filtered_df

def filter_sleep_data(df: pd.DataFrame) -> pd.DataFrame:
    """Filter out samples with missing sleep data."""
    initial_count = len(df)
    
    # Filter out rows where sleep_efficiency or sleep_duration_hours are null/NaN
    mask = df['sleep_efficiency'].notna() & df['sleep_duration_hours'].notna()
    filtered_df = df[mask].copy()
    
    excluded_count = initial_count - len(filtered_df)
    logger.info(f"Sleep data exclusion: {excluded_count} samples removed ({excluded_count/initial_count*100:.2f}%)")
    
    return filtered_df

def merge_otu_and_metadata(otu_df: pd.DataFrame, metadata_df: pd.DataFrame, 
                           sample_id_col: str = 'sample_id') -> pd.DataFrame:
    """Merge OTU table with metadata on sample ID."""
    try:
        merged_df = pd.merge(otu_df, metadata_df, on=sample_id_col, how='inner')
        logger.info(f"Merged {len(merged_df)} samples from OTU and metadata")
        return merged_df
    except Exception as e:
        logger.error(f"Merge failed: {e}")
        raise

def log_exclusion_rates(total_initial: int, excluded_antibiotic: int, 
                       excluded_sleep: int, output_path: Path) -> None:
    """Log exclusion rates to a JSON report file."""
    total_excluded = excluded_antibiotic + excluded_sleep
    exclusion_proportion = total_excluded / total_initial if total_initial > 0 else 0.0
    
    report = {
        "total_initial_sample_count": total_initial,
        "excluded_antibiotic_count": excluded_antibiotic,
        "excluded_sleep_count": excluded_sleep,
        "excluded_count": total_excluded,
        "exclusion_proportion": round(exclusion_proportion, 4)
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Ingestion report saved to {output_path}")
    logger.info(f"Total excluded: {total_excluded} ({exclusion_proportion*100:.2f}%)")

def run_ingestion_pipeline(data_url: str) -> None:
    """Run the full ingestion pipeline."""
    logger.info("Starting ingestion pipeline")
    
    # Ensure output directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Download data
    temp_path = DATA_DIR / "raw_data.csv"
    download_with_backoff(data_url, temp_path)
    
    # Load data
    logger.info("Loading data...")
    df = pd.read_csv(temp_path)
    initial_count = len(df)
    logger.info(f"Loaded {initial_count} samples")
    
    # Verify schema
    required_columns = ['antibiotic_use_last_3m', 'sleep_efficiency', 'sleep_duration_hours']
    headers = df.columns.tolist()
    
    if not verify_schema(headers, required_columns):
        raise ValueError("Schema verification failed")
    
    # Filter antibiotic users
    df_filtered = filter_antibiotic_use(df)
    excluded_antibiotic = initial_count - len(df_filtered)
    
    # Filter missing sleep data
    df_cleaned = filter_sleep_data(df_filtered)
    excluded_sleep = len(df_filtered) - len(df_cleaned)
    
    # Log exclusion rates
    log_exclusion_rates(initial_count, excluded_antibiotic, excluded_sleep, REPORT_PATH)
    
    # Save cleaned dataset
    df_cleaned.to_csv(CLEANED_OUTPUT_PATH, index=False)
    logger.info(f"Cleaned dataset saved to {CLEANED_OUTPUT_PATH}")
    logger.info(f"Final dataset contains {len(df_cleaned)} samples")

def main():
    """Main entry point for ingestion pipeline."""
    # Get data URL from environment or use default
    data_url = os.getenv('DATA_URL', 'https://zenodo.org/record/12345/files/gut_microbiome_sleep_data.csv')
    
    if not data_url:
        logger.error("DATA_URL environment variable not set")
        sys.exit(1)
    
    try:
        run_ingestion_pipeline(data_url)
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
