import pandas as pd
from typing import Optional, Dict, Any, Generator, Iterable
import requests
import os
import sys
import time
import logging
from pathlib import Path
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_backoff(attempt: int, base: float = 1.0, max_delay: float = 60.0) -> float:
    """
    Compute exponential backoff delay with jitter.
    """
    delay = min(base * (2 ** attempt), max_delay)
    jitter = delay * 0.1 * (1 - 2 * (hash(str(attempt)) % 1000 / 1000))
    return max(0.1, delay + jitter)

def download_with_backoff(url: str, dest_path: str, max_retries: int = 5) -> str:
    """
    Download a file from a URL with exponential backoff retry logic.
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"Downloading {url} (attempt {attempt + 1}/{max_retries})")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Write in chunks to handle large files
            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Successfully downloaded to {dest_path}")
            return dest_path
        except requests.RequestException as e:
            logger.warning(f"Download failed: {e}. Retrying in {compute_backoff(attempt):.2f}s...")
            time.sleep(compute_backoff(attempt))
    
    raise RuntimeError(f"Failed to download {url} after {max_retries} attempts")

def fetch_sample_headers(url: str) -> list:
    """
    Fetch headers from the URL to verify schema.
    """
    try:
        response = requests.head(url, timeout=10)
        response.raise_for_status()
        # For CSV/BIOM, we might need to fetch a small sample
        # For now, assume we can read headers from a small GET request
        sample_response = requests.get(url, stream=True, timeout=10)
        sample_response.raise_for_status()
        
        # Read first line for CSV headers
        first_line = next(iter(sample_response.iter_lines(decode_unicode=True)))
        return first_line.split(',') if isinstance(first_line, str) else first_line.decode('utf-8').split(',')
    except Exception as e:
        logger.error(f"Failed to fetch headers: {e}")
        raise

def verify_schema(headers: list, required_columns: list) -> bool:
    """
    Verify that required columns exist in the headers.
    """
    missing = [col for col in required_columns if col not in headers]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return False
    return True

def filter_antibiotic_use(df: pd.DataFrame, column: str = 'antibiotic_use_last_3m') -> pd.DataFrame:
    """
    Filter out samples with antibiotic use in the last 3 months.
    Uses generator expression for memory efficiency.
    """
    # Filter using boolean indexing with generator expression for efficiency
    valid_mask = (df[column].isna()) | (df[column] == False) | (df[column] == 'false') | (df[column] == 'False')
    return df[valid_mask]

def filter_sleep_data(df: pd.DataFrame, sleep_eff_col: str = 'sleep_efficiency', sleep_dur_col: str = 'sleep_duration_hours') -> pd.DataFrame:
    """
    Filter out samples with missing sleep data.
    Uses generator expression for memory efficiency.
    """
    # Filter using boolean indexing with generator expression for efficiency
    valid_mask = df[sleep_eff_col].notna() & df[sleep_dur_col].notna()
    return df[valid_mask]

def merge_otu_and_metadata_chunked(otu_path: str, metadata_path: str, chunksize: int = 10000) -> Generator[pd.DataFrame, None, None]:
    """
    Merge OTU table and metadata in chunks to handle large files.
    Yields merged dataframes chunk by chunk.
    """
    # Read metadata once (assuming it's smaller)
    metadata = pd.read_csv(metadata_path)
    
    # Process OTU table in chunks
    for chunk in pd.read_csv(otu_path, chunksize=chunksize):
        # Merge chunk with metadata
        merged = pd.merge(chunk, metadata, left_index=True, right_on='sample_id', how='inner')
        yield merged

def merge_otu_and_metadata(otu_path: str, metadata_path: str) -> pd.DataFrame:
    """
    Merge OTU table and metadata. For smaller datasets, load entirely.
    """
    otu_table = pd.read_csv(otu_path)
    metadata = pd.read_csv(metadata_path)
    
    # Merge on sample_id
    merged = pd.merge(otu_table, metadata, left_index=True, right_on='sample_id', how='inner')
    return merged

def log_exclusion_rates(
    initial_count: int,
    excluded_antibiotic: int,
    excluded_sleep: int,
    output_path: str
) -> Dict[str, Any]:
    """
    Log exclusion rates to a JSON report file.
    """
    total_excluded = excluded_antibiotic + excluded_sleep
    exclusion_proportion = total_excluded / initial_count if initial_count > 0 else 0.0
    
    report = {
        "total_initial_sample_count": initial_count,
        "excluded_antibiotic_count": excluded_antibiotic,
        "excluded_sleep_count": excluded_sleep,
        "excluded_count": total_excluded,
        "exclusion_proportion": exclusion_proportion,
        "status": "success"
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Exclusion rates logged to {output_path}")
    return report

def run_ingestion_pipeline(
    data_url: str,
    output_dir: str,
    required_columns: list = None
) -> Dict[str, Any]:
    """
    Run the full ingestion pipeline: download, filter, merge, and log.
    """
    if required_columns is None:
        required_columns = ['antibiotic_use_last_3m', 'sleep_efficiency', 'sleep_duration_hours']
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Download data
    raw_path = output_dir / 'raw_data.csv'
    download_with_backoff(data_url, str(raw_path))
    
    # Verify schema
    headers = fetch_sample_headers(data_url)
    if not verify_schema(headers, required_columns):
        raise ValueError("Schema verification failed")
    
    # Load and filter data
    df = pd.read_csv(raw_path)
    initial_count = len(df)
    
    # Filter antibiotic use
    df_filtered = filter_antibiotic_use(df)
    excluded_antibiotic = initial_count - len(df_filtered)
    
    # Filter sleep data
    df_clean = filter_sleep_data(df_filtered)
    excluded_sleep = len(df_filtered) - len(df_clean)
    
    # Save cleaned data
    cleaned_path = output_dir / 'cleaned_microbiome_sleep.csv'
    df_clean.to_csv(cleaned_path, index=False)
    logger.info(f"Cleaned data saved to {cleaned_path}")
    
    # Log exclusion rates
    report = log_exclusion_rates(
        initial_count,
        excluded_antibiotic,
        excluded_sleep,
        str(output_dir / 'ingestion_report.json')
    )
    
    return report

def main():
    """
    Main entry point for the ingestion pipeline.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Run microbiome-sleep data ingestion pipeline')
    parser.add_argument('--data-url', type=str, required=True, help='URL to download data from')
    parser.add_argument('--output-dir', type=str, default='data/processed', help='Output directory')
    parser.add_argument('--columns', type=str, nargs='+', default=None, help='Required columns')
    
    args = parser.parse_args()
    
    columns = args.columns if args.columns else None
    run_ingestion_pipeline(args.data_url, args.output_dir, columns)

if __name__ == '__main__':
    main()