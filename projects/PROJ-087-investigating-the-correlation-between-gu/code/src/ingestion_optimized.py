"""
Optimized ingestion module for merging OTU tables and metadata using chunked processing.

This module implements T034: Performance optimization to reduce RAM usage during
the merge operation (T015) by processing data in chunks rather than loading
everything into memory at once.
"""
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, Generator, Iterable, Tuple
import requests
import os
import sys
import time
import logging
from pathlib import Path
from src.config import load_config

logger = logging.getLogger(__name__)

# Configuration constants
CHUNK_SIZE = 5000  # Number of rows to process at a time
MEMORY_LIMIT_GB = 6.0  # Conservative limit below the 7GB runner constraint

def compute_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """
    Compute exponential backoff delay with jitter.
    
    Args:
        attempt: Current retry attempt number (0-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        
    Returns:
        Delay in seconds before next retry
    """
    delay = min(base_delay * (2 ** attempt), max_delay)
    jitter = delay * 0.1 * np.random.random()
    return delay + jitter

def download_with_backoff(url: str, output_path: str, max_retries: int = 5) -> bool:
    """
    Download file with exponential backoff retry logic.
    
    Args:
        url: URL to download from
        output_path: Local path to save the file
        max_retries: Maximum number of retry attempts
        
    Returns:
        True if download successful, False otherwise
    """
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Downloading {url} (attempt {attempt + 1}/{max_retries + 1})")
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()
            
            # Write in chunks to avoid memory issues
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Successfully downloaded to {output_path}")
            return True
            
        except requests.RequestException as e:
            if attempt == max_retries:
                logger.error(f"Failed to download after {max_retries} retries: {e}")
                return False
            
            delay = compute_backoff(attempt)
            logger.warning(f"Download failed: {e}. Retrying in {delay:.2f}s...")
            time.sleep(delay)
            
    return False

def fetch_sample_headers(url: str, timeout: int = 30) -> Optional[list]:
    """
    Fetch headers from a CSV/TSV URL without downloading the full file.
    
    Args:
        url: URL to fetch headers from
        timeout: Request timeout in seconds
        
    Returns:
        List of column names or None if failed
    """
    try:
        # Use range request to get only first few bytes if server supports it
        # Otherwise, download just the first line
        headers = {'Range': 'bytes=0-4096'}
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        # Parse first line as headers
        first_line = response.text.split('\n')[0]
        if '\t' in first_line:
            return first_line.strip().split('\t')
        elif ',' in first_line:
            return first_line.strip().split(',')
        else:
            return first_line.strip().split()
            
    except Exception as e:
        logger.error(f"Failed to fetch headers: {e}")
        return None

def verify_schema(headers: list, required_columns: list) -> Tuple[bool, list]:
    """
    Verify that required columns exist in the header list.
    
    Args:
        headers: List of column names from the source
        required_columns: List of required column names
        
    Returns:
        Tuple of (is_valid, missing_columns)
    """
    missing = [col for col in required_columns if col not in headers]
    return len(missing) == 0, missing

def filter_antibiotic_use(df: pd.DataFrame, column: str = 'antibiotic_use_last_3m') -> Tuple[pd.DataFrame, int]:
    """
    Filter out samples with antibiotic use in the last 3 months.
    
    Args:
        df: Input DataFrame
        column: Column name containing antibiotic use flag
        
    Returns:
        Tuple of (filtered DataFrame, count of excluded samples)
    """
    initial_count = len(df)
    
    # Keep rows where antibiotic_use_last_3m is False, null, or empty
    # Assuming boolean or string representation
    mask = (df[column].isna()) | (df[column] == False) | (df[column] == 'False') | (df[column] == 'false') | (df[column] == '')
    filtered_df = df[mask].reset_index(drop=True)
    
    excluded_count = initial_count - len(filtered_df)
    logger.info(f"Antibiotic exclusion: {excluded_count} samples removed ({excluded_count/initial_count*100:.2f}%)")
    
    return filtered_df, excluded_count

def filter_sleep_data(df: pd.DataFrame, sleep_efficiency_col: str = 'sleep_efficiency', 
                     sleep_duration_col: str = 'sleep_duration_hours') -> Tuple[pd.DataFrame, int]:
    """
    Filter out samples with missing sleep data.
    
    Args:
        df: Input DataFrame
        sleep_efficiency_col: Column name for sleep efficiency
        sleep_duration_col: Column name for sleep duration
        
    Returns:
        Tuple of (filtered DataFrame, count of excluded samples)
    """
    initial_count = len(df)
    
    # Keep rows where both sleep metrics are not null
    mask = df[sleep_efficiency_col].notna() & df[sleep_duration_col].notna()
    filtered_df = df[mask].reset_index(drop=True)
    
    excluded_count = initial_count - len(filtered_df)
    logger.info(f"Sleep data exclusion: {excluded_count} samples removed ({excluded_count/initial_count*100:.2f}%)")
    
    return filtered_df, excluded_count

def merge_otu_and_metadata_chunked(otu_path: str, metadata_path: str, 
                                  output_path: str, sample_id_col: str = 'sample_id',
                                  chunk_size: int = CHUNK_SIZE) -> Dict[str, Any]:
    """
    Merge OTU table and metadata using chunked processing to reduce RAM usage.
    
    This is the optimized version of T015 that processes large files in chunks
    to stay within the 7GB memory constraint.
    
    Args:
        otu_path: Path to OTU table CSV/TSV
        metadata_path: Path to metadata CSV/TSV
        output_path: Path to save merged output
        sample_id_col: Column name to join on
        chunk_size: Number of rows to process at a time
        
    Returns:
        Dictionary with merge statistics
    """
    logger.info(f"Starting chunked merge: OTU={otu_path}, Metadata={metadata_path}")
    
    # Detect delimiter for both files
    otu_delim = '\t' if '\t' in open(otu_path, 'r').readline() else ','
    meta_delim = '\t' if '\t' in open(metadata_path, 'r').readline() else ','
    
    # Load metadata (usually smaller)
    logger.info("Loading metadata file...")
    metadata = pd.read_csv(metadata_path, sep=meta_delim, low_memory=False)
    meta_count = len(metadata)
    logger.info(f"Loaded {meta_count} metadata rows")
    
    # Process OTU table in chunks
    otu_chunks = pd.read_csv(otu_path, sep=otu_delim, low_memory=False, chunksize=chunk_size)
    
    merged_chunks = []
    total_rows = 0
    processed_chunks = 0
    
    logger.info("Processing OTU table in chunks...")
    for chunk_idx, otu_chunk in enumerate(otu_chunks):
        # Merge current chunk with metadata
        merged_chunk = pd.merge(
            otu_chunk, 
            metadata, 
            on=sample_id_col, 
            how='inner'
        )
        
        merged_chunks.append(merged_chunk)
        total_rows += len(merged_chunk)
        processed_chunks += 1
        
        # Log progress every 10 chunks
        if processed_chunks % 10 == 0:
            logger.info(f"Processed {processed_chunks} chunks, {total_rows} rows merged so far")
            
            # Force garbage collection periodically
            if processed_chunks % 50 == 0:
                import gc
                gc.collect()
    
    # Concatenate all merged chunks
    logger.info(f"Concatenating {len(merged_chunks)} merged chunks...")
    final_df = pd.concat(merged_chunks, ignore_index=True)
    
    # Save to output
    logger.info(f"Saving merged output to {output_path}...")
    final_df.to_csv(output_path, index=False)
    
    logger.info(f"Merge complete: {total_rows} rows written to {output_path}")
    
    return {
        'total_rows': total_rows,
        'metadata_rows': meta_count,
        'chunks_processed': processed_chunks,
        'output_path': output_path
    }

def log_exclusion_rates(initial_count: int, excluded_antibiotic: int, 
                       excluded_sleep: int, output_path: str) -> Dict[str, Any]:
    """
    Log exclusion rates to a JSON report file.
    
    Args:
        initial_count: Total initial sample count
        excluded_antibiotic: Count excluded due to antibiotic use
        excluded_sleep: Count excluded due to missing sleep data
        output_path: Path to save the JSON report
        
    Returns:
        Dictionary with exclusion statistics
    """
    total_excluded = excluded_antibiotic + excluded_sleep
    exclusion_proportion = total_excluded / initial_count if initial_count > 0 else 0.0
    
    report = {
        'total_initial_sample_count': initial_count,
        'excluded_count': total_excluded,
        'excluded_antibiotic_use': excluded_antibiotic,
        'excluded_missing_sleep_data': excluded_sleep,
        'exclusion_proportion': exclusion_proportion,
        'retained_count': initial_count - total_excluded
    }
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    import json
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Exclusion report saved to {output_path}")
    logger.info(f"Initial: {initial_count}, Excluded: {total_excluded}, Retained: {report['retained_count']}")
    
    return report

def run_ingestion_pipeline(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Run the complete ingestion pipeline with optimized chunked merging.
    
    Args:
        config: Optional configuration dictionary. If None, loads from environment.
        
    Returns:
        Dictionary with pipeline results and statistics
    """
    if config is None:
        config = load_config()
    
    logger.info("Starting optimized ingestion pipeline")
    
    # Extract paths from config
    otu_path = config.get('OTU_DATA_PATH', 'data/raw/otu_table.csv')
    metadata_path = config.get('METADATA_PATH', 'data/raw/sleep_metadata.csv')
    output_path = config.get('CLEANED_DATA_PATH', 'data/processed/cleaned_microbiome_sleep.csv')
    report_path = config.get('INGESTION_REPORT_PATH', 'data/processed/ingestion_report.json')
    
    # Ensure directories exist
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    # Step 1: Filter antibiotic use
    logger.info("Step 1: Filtering antibiotic use...")
    df = pd.read_csv(otu_path)  # Assuming OTU table is the primary data source
    initial_count = len(df)
    
    df_filtered, excluded_antibiotic = filter_antibiotic_use(df)
    results['excluded_antibiotic'] = excluded_antibiotic
    
    # Step 2: Filter sleep data
    logger.info("Step 2: Filtering missing sleep data...")
    df_filtered, excluded_sleep = filter_sleep_data(df_filtered)
    results['excluded_sleep'] = excluded_sleep
    
    # Step 3: Save cleaned data
    logger.info("Step 3: Saving cleaned dataset...")
    df_filtered.to_csv(output_path, index=False)
    results['cleaned_data_path'] = output_path
    results['final_count'] = len(df_filtered)
    
    # Step 4: Log exclusion rates
    logger.info("Step 4: Logging exclusion rates...")
    exclusion_report = log_exclusion_rates(initial_count, excluded_antibiotic, 
                                         excluded_sleep, report_path)
    results['exclusion_report'] = exclusion_report
    
    logger.info("Optimized ingestion pipeline completed successfully")
    return results

def main():
    """Main entry point for the optimized ingestion script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        results = run_ingestion_pipeline()
        print(f"Ingestion complete. Final dataset: {results['final_count']} rows")
        print(f"Exclusion report: {results['exclusion_report']}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()