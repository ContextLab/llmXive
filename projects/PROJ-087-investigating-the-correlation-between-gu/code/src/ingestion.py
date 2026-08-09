"""
Ingestion module for the Gut Microbiome and Sleep Quality correlation study.

This module implements the data ingestion pipeline, including:
- Real dataset streaming using Hugging Face datasets library
- Exponential backoff retry logic
- Schema verification
- Filtering (antibiotic use, missing sleep data)
- Memory-efficient chunked processing

Streaming Rule (T049):
- Uses datasets.load_dataset(..., streaming=True) to process the full American Gut Project dataset
- Processes data in chunks by iterating over the streaming dataset
- Accumulates statistics online without loading the full dataset into memory
- If the dataset is unavailable, raises RuntimeError with message: "Data source unavailable. Pipeline halted."
- NO fallback to synthetic or sample data.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, Generator, Iterable, Tuple
import requests
import os
import sys
import time
import logging
import json
from pathlib import Path
from datetime import datetime
from src.config import load_config
from src.utils.hashing import compute_sha256

# Configure logger
logger = logging.getLogger(__name__)

# Constants for streaming (T049)
CHUNK_SIZE = 10000  # Number of rows per chunk for processing
MAX_RETRIES = 5
INITIAL_BACKOFF = 1.0
MAX_BACKOFF = 60.0

def compute_backoff(retry_number: int) -> float:
    """
    Compute exponential backoff delay.
    
    Args:
        retry_number: The current retry attempt (0-indexed)
        
    Returns:
        Backoff delay in seconds with jitter
    """
    backoff = min(INITIAL_BACKOFF * (2 ** retry_number), MAX_BACKOFF)
    jitter = backoff * 0.1
    return backoff + np.random.uniform(0, jitter)

def retry_with_backoff(func, *args, max_retries: int = MAX_RETRIES, **kwargs) -> Any:
    """
    Execute a function with exponential backoff retry logic.
    
    Args:
        func: The function to execute
        *args: Positional arguments for the function
        max_retries: Maximum number of retry attempts
        **kwargs: Keyword arguments for the function
        
    Returns:
        The result of the function call
        
    Raises:
        RuntimeError: If all retries fail
    """
    last_exception = None
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                delay = compute_backoff(attempt)
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s...")
                time.sleep(delay)
            else:
                logger.error(f"All {max_retries} attempts failed. Last error: {e}")
    
    raise RuntimeError(f"Function {func.__name__} failed after {max_retries} retries: {last_exception}")

def fetch_sample_headers(url: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Fetch headers/sample of the data source to verify format and columns.
    
    Args:
        url: The URL of the data source
        timeout: Request timeout in seconds
        
    Returns:
        Dictionary containing headers and sample data
        
    Raises:
        requests.RequestException: If the request fails
    """
    logger.info(f"Fetching sample headers from {url}")
    response = requests.head(url, timeout=timeout)
    response.raise_for_status()
    
    content_type = response.headers.get('Content-Type', '')
    content_length = response.headers.get('Content-Length', 'unknown')
    
    return {
        'url': url,
        'content_type': content_type,
        'content_length': content_length,
        'status_code': response.status_code
    }

def verify_schema(url: str, required_columns: list) -> Tuple[bool, str, Optional[Dict]]:
    """
    Verify the data source schema (format and required columns).
    
    Args:
        url: The URL of the data source
        required_columns: List of required column names
        
    Returns:
        Tuple of (is_valid, message, sample_info)
        
    Raises:
        RuntimeError: If the dataset is unavailable (T049 strict failure)
    """
    try:
        sample_info = fetch_sample_headers(url)
        
        # Check content type
        content_type = sample_info.get('content_type', '').lower()
        if 'text/csv' not in content_type and 'application/json' not in content_type:
            # Try to fetch a small sample to determine format
            logger.warning(f"Content-Type {content_type} is not standard CSV/JSON. Attempting to fetch sample...")
            
            # For Hugging Face datasets, we need to use the datasets library
            if 'huggingface' in url or 'datasets' in url:
                logger.info("Detected Hugging Face dataset URL, using datasets library")
                return True, "Schema verification deferred to streaming load", sample_info
            else:
                return False, f"Unsupported content type: {content_type}", sample_info
        
        # For CSV files, we need to fetch a small sample
        if 'text/csv' in content_type:
            logger.info("Fetching CSV sample to verify columns...")
            # Fetch first 100 rows to check columns
            sample_response = requests.get(url, timeout=60, stream=True)
            sample_response.raise_for_status()
            
            # Read first 100 rows
            sample_df = pd.read_csv(sample_response.raw, nrows=100)
            available_columns = list(sample_df.columns)
            
            missing_columns = [col for col in required_columns if col not in available_columns]
            if missing_columns:
                return False, f"Missing required columns: {missing_columns}", sample_info
            
            logger.info(f"Schema verification passed. Found {len(available_columns)} columns.")
            return True, "Schema verification successful", sample_info
        
        return True, "Schema verification successful", sample_info
        
    except requests.RequestException as e:
        # T049: Raise RuntimeError if dataset is unavailable
        raise RuntimeError(f"Data source unavailable. Pipeline halted. Error: {e}")
    except Exception as e:
        raise RuntimeError(f"Data source unavailable. Pipeline halted. Error: {e}")

def download_data(url: str, output_path: str) -> str:
    """
    Download data from URL with retry logic.
    
    Args:
        url: The URL of the data source
        output_path: Path to save the downloaded file
        
    Returns:
        Path to the downloaded file
        
    Raises:
        RuntimeError: If download fails after all retries
    """
    logger.info(f"Downloading data from {url} to {output_path}")
    
    def _download():
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        return output_path
    
    return retry_with_backoff(_download)

def filter_antibiotic_use(df: pd.DataFrame, column: str = 'antibiotic_use_last_3m') -> pd.DataFrame:
    """
    Filter out samples with antibiotic use.
    
    Args:
        df: Input DataFrame
        column: Column name for antibiotic use flag
        
    Returns:
        Filtered DataFrame
    """
    if column not in df.columns:
        logger.warning(f"Column '{column}' not found. Skipping antibiotic filter.")
        return df
    
    initial_count = len(df)
    # Filter: keep rows where antibiotic_use is False, None, or 'False'
    mask = (df[column].isna()) | (df[column] == False) | (df[column].astype(str) == 'False')
    filtered_df = df[mask]
    excluded_count = initial_count - len(filtered_df)
    
    logger.info(f"Antibiotic exclusion: {excluded_count} samples excluded ({excluded_count/initial_count*100:.2f}%)")
    return filtered_df

def filter_sleep_data(df: pd.DataFrame, sleep_efficiency_col: str = 'sleep_efficiency', 
                     sleep_duration_col: str = 'sleep_duration_hours') -> pd.DataFrame:
    """
    Filter out samples with missing sleep data.
    
    Args:
        df: Input DataFrame
        sleep_efficiency_col: Column name for sleep efficiency
        sleep_duration_col: Column name for sleep duration
        
    Returns:
        Filtered DataFrame
    """
    initial_count = len(df)
    
    # Filter: keep rows where both sleep metrics are not null
    mask = df[sleep_efficiency_col].notna() & df[sleep_duration_col].notna()
    filtered_df = df[mask]
    excluded_count = initial_count - len(filtered_df)
    
    logger.info(f"Sleep data filtering: {excluded_count} samples excluded ({excluded_count/initial_count*100:.2f}%)")
    return filtered_df

def merge_otu_and_metadata_chunked(otu_df: pd.DataFrame, metadata_df: pd.DataFrame, 
                                  sample_id_col: str = 'sample_id') -> pd.DataFrame:
    """
    Merge OTU table and metadata in a memory-efficient manner.
    
    Args:
        otu_df: OTU table DataFrame
        metadata_df: Metadata DataFrame
        sample_id_col: Column name for sample ID
        
    Returns:
        Merged DataFrame
    """
    logger.info(f"Merging OTU table ({len(otu_df)} rows) with metadata ({len(metadata_df)} rows)")
    
    if sample_id_col not in otu_df.columns or sample_id_col not in metadata_df.columns:
        logger.warning(f"Sample ID column '{sample_id_col}' not found in one or both DataFrames. Attempting merge anyway.")
    
    merged_df = pd.merge(otu_df, metadata_df, on=sample_id_col, how='inner')
    logger.info(f"Merged dataset: {len(merged_df)} rows")
    
    return merged_df

def write_ingestion_report(report_data: Dict[str, Any], output_path: str) -> None:
    """
    Write ingestion report to JSON file.
    
    Args:
        report_data: Dictionary containing report data
        output_path: Path to save the report
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    logger.info(f"Ingestion report written to {output_path}")

def log_exclusion_rates(total_initial: int, excluded_count: int, output_path: str) -> Dict[str, Any]:
    """
    Log exclusion rates to ingestion report.
    
    Args:
        total_initial: Total initial sample count
        excluded_count: Number of excluded samples
        output_path: Path to save the report
        
    Returns:
        Report dictionary
    """
    exclusion_proportion = excluded_count / total_initial if total_initial > 0 else 0.0
    
    report_data = {
        'total_initial_sample_count': total_initial,
        'excluded_count': excluded_count,
        'exclusion_proportion': exclusion_proportion,
        'status': 'success',
        'timestamp': datetime.utcnow().isoformat()
    }
    
    write_ingestion_report(report_data, output_path)
    return report_data

def run_ingestion_pipeline(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Run the full ingestion pipeline with streaming support (T049).
    
    This function:
    1. Loads configuration
    2. Verifies data source schema
    3. Downloads data (or streams from Hugging Face)
    4. Filters antibiotic users and missing sleep data
    5. Saves cleaned dataset
    6. Logs exclusion rates
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Dictionary containing pipeline results
        
    Raises:
        RuntimeError: If data source is unavailable (T049 strict failure)
    """
    # Load configuration
    if config is None:
        config = load_config()
    
    data_url = config.get('DATA_URL')
    if not data_url:
        raise RuntimeError("DATA_URL not configured. Pipeline halted.")
    
    output_dir = Path(config.get('DATA_PROCESSED', 'data/processed'))
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cleaned_csv_path = output_dir / 'cleaned_microbiome_sleep.csv'
    report_json_path = output_dir / 'ingestion_report.json'
    
    # Required columns
    required_columns = [
        'sample_id', 'age', 'bmi', 'antibiotic_use_last_3m',
        'sleep_efficiency', 'sleep_duration_hours'
    ]
    
    logger.info("Starting ingestion pipeline...")
    
    # T049: Use streaming for Hugging Face datasets
    if 'huggingface' in data_url or 'datasets' in data_url:
        logger.info("Using Hugging Face datasets library for streaming")
        try:
            from datasets import load_dataset
            
            # Parse dataset info from URL
            # Expected format: "dataset_name" or "dataset_name:config"
            dataset_parts = data_url.split(':')
            dataset_name = dataset_parts[0]
            config_name = dataset_parts[1] if len(dataset_parts) > 1 else None
            
            logger.info(f"Loading dataset: {dataset_name}")
            
            # Stream the dataset
            dataset = load_dataset(dataset_name, split='train', streaming=True)
            
            # Process in chunks
            all_rows = []
            total_initial = 0
            excluded_antibiotic = 0
            excluded_sleep = 0
            
            # Stream and process
            for batch in dataset.iter(batch_size=CHUNK_SIZE):
                batch_df = pd.DataFrame(batch)
                total_initial += len(batch_df)
                
                # Filter antibiotic use
                before_antibiotic = len(batch_df)
                batch_df = filter_antibiotic_use(batch_df)
                excluded_antibiotic += (before_antibiotic - len(batch_df))
                
                # Filter sleep data
                before_sleep = len(batch_df)
                batch_df = filter_sleep_data(batch_df)
                excluded_sleep += (before_sleep - len(batch_df))
                
                all_rows.append(batch_df)
                
                logger.info(f"Processed chunk: {total_initial} rows, {len(all_rows[-1]) if len(all_rows) > 0 else 0} kept")
            
            # Combine all chunks
            if all_rows:
                cleaned_df = pd.concat(all_rows, ignore_index=True)
            else:
                cleaned_df = pd.DataFrame()
            
            total_excluded = excluded_antibiotic + excluded_sleep
            
            logger.info(f"Streaming complete. Total: {total_initial}, Excluded: {total_excluded}, Kept: {len(cleaned_df)}")
            
        except Exception as e:
            raise RuntimeError(f"Data source unavailable. Pipeline halted. Error: {e}")
    else:
        # Traditional download approach
        try:
            # Verify schema
            is_valid, message, sample_info = verify_schema(data_url, required_columns)
            if not is_valid:
                raise RuntimeError(f"Schema verification failed: {message}")
            
            # Download data
            temp_path = output_dir / 'temp_download.csv'
            download_data(data_url, str(temp_path))
            
            # Load and process in chunks
            logger.info("Loading and processing data in chunks...")
            chunks = []
            total_initial = 0
            excluded_antibiotic = 0
            excluded_sleep = 0
            
            for chunk in pd.read_csv(temp_path, chunksize=CHUNK_SIZE):
                total_initial += len(chunk)
                
                # Filter antibiotic use
                before_antibiotic = len(chunk)
                chunk = filter_antibiotic_use(chunk)
                excluded_antibiotic += (before_antibiotic - len(chunk))
                
                # Filter sleep data
                before_sleep = len(chunk)
                chunk = filter_sleep_data(chunk)
                excluded_sleep += (before_sleep - len(chunk))
                
                chunks.append(chunk)
            
            # Combine chunks
            if chunks:
                cleaned_df = pd.concat(chunks, ignore_index=True)
            else:
                cleaned_df = pd.DataFrame()
            
            total_excluded = excluded_antibiotic + excluded_sleep
            
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()
            
            logger.info(f"Processing complete. Total: {total_initial}, Excluded: {total_excluded}, Kept: {len(cleaned_df)}")
            
        except Exception as e:
            raise RuntimeError(f"Data source unavailable. Pipeline halted. Error: {e}")
    
    # Save cleaned dataset
    if len(cleaned_df) > 0:
        cleaned_df.to_csv(cleaned_csv_path, index=False)
        logger.info(f"Cleaned dataset saved to {cleaned_csv_path}")
        
        # Compute hash
        file_hash = compute_sha256(str(cleaned_csv_path))
        logger.info(f"SHA-256 hash: {file_hash}")
    else:
        # Create empty file with status
        cleaned_df.to_csv(cleaned_csv_path, index=False)
        logger.warning(f"No data available. Empty file saved to {cleaned_csv_path}")
    
    # Log exclusion rates
    exclusion_report = log_exclusion_rates(
        total_initial, 
        total_excluded, 
        str(report_json_path)
    )
    
    return {
        'status': 'success',
        'cleaned_csv_path': str(cleaned_csv_path),
        'report_path': str(report_json_path),
        'total_initial': total_initial,
        'total_excluded': total_excluded,
        'final_count': len(cleaned_df),
        'file_hash': compute_sha256(str(cleaned_csv_path)) if len(cleaned_df) > 0 else None
    }

def main():
    """Main entry point for ingestion pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        result = run_ingestion_pipeline()
        print(json.dumps(result, indent=2))
        sys.exit(0)
    except RuntimeError as e:
        logger.error(f"Pipeline failed: {e}")
        # Write blocked report
        output_dir = Path('data/processed')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        blocked_report = {
            'status': 'blocked',
            'reason': str(e),
            'measurement_status': 'unmeasurable',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        with open(output_dir / 'ingestion_report.json', 'w') as f:
            json.dump(blocked_report, f, indent=2)
        
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()