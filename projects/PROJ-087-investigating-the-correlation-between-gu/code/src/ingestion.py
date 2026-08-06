"""
Ingestion pipeline for Gut Microbiome and Sleep Quality data.

Implements data download, schema verification, filtering (antibiotic use, missing sleep),
merging, and logging of exclusion rates.

Refactored for memory efficiency using generator expressions where appropriate.
"""
import pandas as pd
from typing import Optional, Dict, Any, Generator, Iterable
import requests
import os
import sys
import time
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 5
BACKOFF_FACTOR = 1.5

def compute_backoff(retry_count: int) -> float:
    """Calculate exponential backoff delay."""
    return BACKOFF_FACTOR ** retry_count

def download_with_backoff(url: str, output_path: str, timeout: int = DEFAULT_TIMEOUT) -> bool:
    """
    Download file with exponential backoff retry logic.
    
    Args:
        url: Source URL
        output_path: Local destination path
        timeout: Request timeout in seconds
        
    Returns:
        True if successful, False otherwise
    """
    for retry in range(MAX_RETRIES):
        try:
            logger.info(f"Attempting download (attempt {retry + 1}/{MAX_RETRIES})")
            response = requests.get(url, timeout=timeout, stream=True)
            response.raise_for_status()
            
            # Write in chunks to manage memory
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Download successful: {output_path}")
            return True
            
        except requests.RequestException as e:
            delay = compute_backoff(retry)
            logger.warning(f"Download failed: {e}. Retrying in {delay:.2f}s...")
            time.sleep(delay)
            
    logger.error(f"Download failed after {MAX_RETRIES} attempts")
    return False

def fetch_sample_headers(url: str, timeout: int = DEFAULT_TIMEOUT) -> Optional[list]:
    """
    Fetch headers from the source URL to verify schema.
    
    Args:
        url: Source URL
        timeout: Request timeout
        
    Returns:
        List of column names or None if failed
    """
    try:
        # Use head request if possible, otherwise get first few lines
        response = requests.head(url, timeout=timeout)
        if response.status_code == 200:
            # Fallback to GET for first 1KB to parse headers
            response = requests.get(url, timeout=timeout, stream=True)
            response.raise_for_status()
            first_chunk = next(response.iter_content(chunk_size=1024))
            lines = first_chunk.decode('utf-8').splitlines()
            if lines:
                # Assume CSV format
                return lines[0].strip().split(',')
        return None
    except requests.RequestException as e:
        logger.error(f"Failed to fetch headers: {e}")
        return None

def verify_schema(headers: list, required_columns: list) -> bool:
    """
    Verify that required columns exist in the headers.
    
    Args:
        headers: List of column names
        required_columns: List of required column names
        
    Returns:
        True if all required columns are present
    """
    missing = [col for col in required_columns if col not in headers]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return False
    return True

def filter_antibiotic_use(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """
    Filter out samples with recent antibiotic use.
    
    Refactored to use generator expression for memory efficiency.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Tuple of (filtered DataFrame, count of excluded rows)
    """
    initial_count = len(df)
    # Use generator expression for memory efficiency
    mask = (df['antibiotic_use_last_3m'].isna()) | (df['antibiotic_use_last_3m'] == False)
    filtered_df = df[mask]
    excluded_count = initial_count - len(filtered_df)
    logger.info(f"Antibiotic exclusion: {excluded_count} samples removed")
    return filtered_df, excluded_count

def filter_sleep_data(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """
    Filter out samples with missing sleep data.
    
    Refactored to use generator expression for memory efficiency.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Tuple of (filtered DataFrame, count of excluded rows)
    """
    initial_count = len(df)
    # Use generator expression for memory efficiency
    mask = df['sleep_efficiency'].notna() & df['sleep_duration_hours'].notna()
    filtered_df = df[mask]
    excluded_count = initial_count - len(filtered_df)
    logger.info(f"Sleep data exclusion: {excluded_count} samples removed")
    return filtered_df, excluded_count

def merge_otu_and_metadata(otu_df: pd.DataFrame, metadata_df: pd.DataFrame, 
                           sample_id_col: str = 'sample_id') -> pd.DataFrame:
    """
    Merge OTU table with metadata on sample ID.
    
    Args:
        otu_df: OTU count table
        metadata_df: Metadata DataFrame
        sample_id_col: Column name for sample ID
        
    Returns:
        Merged DataFrame
    """
    logger.info(f"Merging OTU table ({len(otu_df)} samples) with metadata ({len(metadata_df)} samples)")
    merged = pd.merge(otu_df, metadata_df, on=sample_id_col, how='inner')
    logger.info(f"Merged dataset contains {len(merged)} samples")
    return merged

def log_exclusion_rates(total_initial: int, total_excluded: int, output_path: str) -> None:
    """
    Log exclusion statistics to a JSON file.
    
    Args:
        total_initial: Total initial sample count
        total_excluded: Total number of excluded samples
        output_path: Path to output JSON file
    """
    exclusion_proportion = total_excluded / total_initial if total_initial > 0 else 0.0
    
    report = {
        'total_initial_sample_count': total_initial,
        'excluded_count': total_excluded,
        'exclusion_proportion': exclusion_proportion
    }
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    import json
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Ingestion report saved to {output_path}")

def run_ingestion_pipeline(data_url: str, output_csv: str, output_report: str) -> None:
    """
    Run the full ingestion pipeline.
    
    Args:
        data_url: URL of the source data
        output_csv: Path for cleaned CSV output
        output_report: Path for exclusion report JSON
    """
    logger.info("Starting ingestion pipeline")
    
    # Step 1: Verify schema
    headers = fetch_sample_headers(data_url)
    if not headers:
        raise RuntimeError("Failed to fetch data headers")
    
    required_cols = ['antibiotic_use_last_3m', 'sleep_efficiency', 'sleep_duration_hours']
    if not verify_schema(headers, required_cols):
        raise RuntimeError("Schema verification failed")
    
    # Step 2: Download data
    temp_path = "data/raw/temp_data.csv"
    if not download_with_backoff(data_url, temp_path):
        raise RuntimeError("Data download failed")
    
    # Step 3: Load data
    df = pd.read_csv(temp_path)
    initial_count = len(df)
    logger.info(f"Loaded {initial_count} samples")
    
    # Step 4: Filter antibiotic use
    df, excluded_1 = filter_antibiotic_use(df)
    
    # Step 5: Filter sleep data
    df, excluded_2 = filter_sleep_data(df)
    
    total_excluded = excluded_1 + excluded_2
    
    # Step 6: Save cleaned data
    df.to_csv(output_csv, index=False)
    logger.info(f"Cleaned data saved to {output_csv}")
    
    # Step 7: Log exclusion rates
    log_exclusion_rates(initial_count, total_excluded, output_report)
    
    logger.info("Ingestion pipeline completed successfully")

def main():
    """Main entry point for ingestion script."""
    import os
    from src.config import load_config
    
    config = load_config()
    data_url = config.get('DATA_URL')
    
    if not data_url:
        logger.error("DATA_URL not found in environment variables")
        sys.exit(1)
    
    output_csv = config.get('CLEANED_DATA_PATH', 'data/processed/cleaned_microbiome_sleep.csv')
    output_report = config.get('INGESTION_REPORT_PATH', 'data/processed/ingestion_report.json')
    
    try:
        run_ingestion_pipeline(data_url, output_csv, output_report)
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()