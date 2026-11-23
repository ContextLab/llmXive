"""
Ingestion module for Gut Microbiome and Sleep Quality correlation study.

Implements real dataset streaming using the Hugging Face datasets library to process
the American Gut Project data in chunks, ensuring memory efficiency while adhering
to the ~7 GB RAM constraint.

Streaming Rule:
- Uses datasets.load_dataset(..., streaming=True) to iterate over the dataset.
- Processes data in logical batches (conceptual chunks) to avoid loading the full
  dataset into memory at once.
- If the real data source is unavailable, raises RuntimeError with a clear message.
- NO synthetic data generation or fallback to mock data is permitted.
"""
import os
import sys
import logging
import time
import requests
import json
import pandas as pd
from typing import Optional, Dict, Any, Generator, Iterable, Tuple
from datasets import load_dataset
from pathlib import Path

# Import from local project structure
from src.config import load_config
from src.logging_config import setup_logger
from src.utils.hashing import compute_sha256

logger = setup_logger(__name__)

# Constants
CHUNK_SIZE = 10000  # Number of rows to process at a time for memory efficiency
MAX_RETRIES = 5
BASE_BACKOFF = 1.0  # seconds

def compute_backoff(retry_count: int) -> float:
    """Compute exponential backoff delay."""
    return BASE_BACKOFF * (2 ** retry_count)

def retry_with_backoff(func, *args, **kwargs) -> Any:
    """
    Execute a function with exponential backoff retry logic.
    
    Args:
        func: The function to execute.
        *args: Positional arguments for the function.
        **kwargs: Keyword arguments for the function.
        
    Returns:
        The result of the function if successful.
        
    Raises:
        RuntimeError: If the function fails after MAX_RETRIES attempts.
    """
    last_exception = None
    for attempt in range(MAX_RETRIES):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < MAX_RETRIES - 1:
                delay = compute_backoff(attempt)
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s...")
                time.sleep(delay)
            else:
                logger.error(f"Failed after {MAX_RETRIES} attempts.")
                raise RuntimeError(f"Data fetch failed after {MAX_RETRIES} retries: {e}") from e
    raise RuntimeError("Unexpected error in retry logic")

def fetch_sample_headers(url: str) -> Dict[str, Any]:
    """
    Fetch headers or a sample of the dataset to verify existence and schema.
    
    Args:
        url: The URL or dataset identifier.
        
    Returns:
        A dictionary containing schema information.
        
    Raises:
        RuntimeError: If the dataset is not accessible.
    """
    logger.info(f"Verifying data source accessibility: {url}")
    try:
        # Attempt to load dataset info via streaming (does not download full data)
        # This checks if the dataset exists and is accessible
        ds = load_dataset(url, split="train", streaming=True)
        # Try to get a sample to verify columns
        sample = next(iter(ds))
        logger.info(f"Dataset accessible. Sample keys: {list(sample.keys())}")
        return {"status": "accessible", "keys": list(sample.keys())}
    except Exception as e:
        logger.error(f"Data source verification failed: {e}")
        raise RuntimeError("Data source unavailable. Pipeline halted.") from e

def verify_schema(url: str, required_columns: list) -> bool:
    """
    Verify that the dataset contains the required columns.
    
    Args:
        url: The dataset identifier.
        required_columns: List of column names that must exist.
        
    Returns:
        True if all required columns are present.
        
    Raises:
        RuntimeError: If the schema is missing required columns.
    """
    try:
        ds = load_dataset(url, split="train", streaming=True)
        sample = next(iter(ds))
        available_cols = set(sample.keys())
        missing = set(required_columns) - available_cols
        
        if missing:
            logger.error(f"Schema verification failed. Missing columns: {missing}")
            raise RuntimeError(f"Schema mismatch: Missing required columns {missing}")
        
        logger.info("Schema verification successful.")
        return True
    except RuntimeError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during schema verification: {e}")
        raise RuntimeError("Data source unavailable. Pipeline halted.") from e

def download_data(url: str) -> Generator[Dict[str, Any], None, None]:
    """
    Download and yield data chunks from the dataset.
    
    This function uses the Hugging Face datasets library with streaming enabled
    to process the American Gut Project (or similar) dataset in chunks.
    
    Args:
        url: The dataset identifier (e.g., 'american_gut_project' or a URL).
        
    Yields:
        Dictionaries representing rows of data.
        
    Raises:
        RuntimeError: If the data source is unavailable.
    """
    logger.info(f"Starting data streaming from: {url}")
    try:
        # Load dataset in streaming mode
        # Note: The actual dataset name/revision should be provided in config or env
        ds = load_dataset(url, split="train", streaming=True)
        
        for row in ds:
            yield row
            
    except Exception as e:
        logger.error(f"Failed to stream data: {e}")
        raise RuntimeError("Data source unavailable. Pipeline halted.") from e

def filter_antibiotic_use(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out samples with recent antibiotic use.
    
    Args:
        df: DataFrame containing sample data.
        
    Returns:
        Filtered DataFrame.
    """
    mask = df['antibiotic_use_last_3m'].isna() | (df['antibiotic_use_last_3m'] == False)
    return df[mask]

def filter_sleep_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out samples with missing sleep data.
    
    Args:
        df: DataFrame containing sample data.
        
    Returns:
        Filtered DataFrame.
    """
    mask = df['sleep_efficiency'].notna() & df['sleep_duration_hours'].notna()
    return df[mask]

def merge_otu_and_metadata_chunked(otu_iter: Iterable, meta_iter: Iterable, chunk_size: int = CHUNK_SIZE) -> Generator[pd.DataFrame, None, None]:
    """
    Merge OTU tables and metadata in a memory-efficient chunked manner.
    
    Args:
        otu_iter: Iterable of OTU data rows.
        meta_iter: Iterable of metadata rows.
        chunk_size: Number of rows to process at a time.
        
    Yields:
        Merged DataFrames for each chunk.
    """
    # This is a simplified implementation. In a real scenario, we would need to
    # align OTU and metadata by sample_id. For this task, we assume the streaming
    # yields already joined data or we perform a join on the fly.
    # Given the constraints, we will simulate the chunked processing logic.
    
    chunk = []
    for i, row in enumerate(otu_iter):
        chunk.append(row)
        if len(chunk) >= chunk_size:
            yield pd.DataFrame(chunk)
            chunk = []
    if chunk:
        yield pd.DataFrame(chunk)

def run_ingestion_pipeline(url: str, output_path: str, report_path: str) -> Dict[str, Any]:
    """
    Run the full ingestion pipeline with streaming.
    
    Args:
        url: The dataset identifier.
        output_path: Path to save the cleaned dataset.
        report_path: Path to save the ingestion report.
        
    Returns:
        A dictionary containing pipeline statistics.
    """
    required_columns = ['sample_id', 'age', 'bmi', 'antibiotic_use_last_3m', 
                        'sleep_efficiency', 'sleep_duration_hours']
    
    # Step 1: Verify source
    logger.info("Step 1: Verifying data source...")
    retry_with_backoff(fetch_sample_headers, url)
    retry_with_backoff(verify_schema, url, required_columns)
    
    # Step 2: Stream, filter, and save
    logger.info("Step 2: Streaming, filtering, and saving data...")
    
    total_rows = 0
    excluded_antibiotic = 0
    excluded_sleep = 0
    
    # We will collect filtered data in chunks to write to CSV efficiently
    # Since pandas write_csv doesn't support incremental writes easily without mode='a',
    # we will accumulate a buffer and write in chunks.
    
    buffer = []
    buffer_size = 10000
    
    try:
        ds = load_dataset(url, split="train", streaming=True)
        
        for row in ds:
            total_rows += 1
            
            # Apply filters
            # Note: row is a dict. We convert to a single-row DataFrame for filtering logic
            # or apply logic directly.
            
            # Antibiotic filter
            if row.get('antibiotic_use_last_3m') is not None and row.get('antibiotic_use_last_3m') is True:
                excluded_antibiotic += 1
                continue
            
            # Sleep filter
            if pd.isna(row.get('sleep_efficiency')) or pd.isna(row.get('sleep_duration_hours')):
                excluded_sleep += 1
                continue
                
            buffer.append(row)
            
            if len(buffer) >= buffer_size:
                df_chunk = pd.DataFrame(buffer)
                # Append to file (create if not exists)
                mode = 'a' if Path(output_path).exists() else 'w'
                header = mode == 'w'
                df_chunk.to_csv(output_path, mode=mode, index=False, header=header)
                buffer = []
        
        # Write remaining buffer
        if buffer:
            df_chunk = pd.DataFrame(buffer)
            mode = 'a' if Path(output_path).exists() else 'w'
            header = mode == 'w'
            df_chunk.to_csv(output_path, mode=mode, index=False, header=header)
            
    except Exception as e:
        logger.error(f"Error during data processing: {e}")
        raise RuntimeError("Data source unavailable. Pipeline halted.") from e
        
    final_count = total_rows - excluded_antibiotic - excluded_sleep
    
    # Step 3: Generate Report
    report = {
        "status": "success",
        "total_initial_sample_count": total_rows,
        "excluded_antibiotic": excluded_antibiotic,
        "excluded_sleep": excluded_sleep,
        "exclusion_proportion": (excluded_antibiotic + excluded_sleep) / total_rows if total_rows > 0 else 0,
        "final_row_count": final_count,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    logger.info(f"Ingestion complete. Saved {final_count} rows to {output_path}")
    return report

def main():
    """Main entry point for the ingestion script."""
    config = load_config()
    url = config.get('DATA_URL')
    
    if not url:
        raise RuntimeError("DATA_URL not configured. Please set DATA_URL in environment or config.")
        
    output_path = str(Path(config['DATA_DIR']) / 'processed' / 'cleaned_microbiome_sleep.csv')
    report_path = str(Path(config['DATA_DIR']) / 'processed' / 'ingestion_report.json')
    
    # Ensure directories exist
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    run_ingestion_pipeline(url, output_path, report_path)

if __name__ == "__main__":
    main()
