"""
Performance optimization module for PROJ-540.

Implements vectorized pandas operations and chunked processing
for large datasets to ensure < 60s processing time on 10k records.
"""
import pandas as pd
import numpy as np
import logging
import time
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from config import load_config, ensure_directories, get_dataset_url
from ingest import parse_and_validate
from clean import apply_listwise_deletion, load_cleaned_data, save_cleaned_data
from exceptions import PowerLimitationError

logger = logging.getLogger(__name__)

def vectorize_cleaning_operations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Vectorize common cleaning operations that were previously row-wise.
    
    Replaces inefficient apply() calls with vectorized numpy/pandas operations.
    """
    logger.info("Applying vectorized cleaning operations...")
    start_time = time.time()
    
    # Vectorized numeric conversion instead of apply
    numeric_cols = ['news_exposure_freq', 'anxiety_score', 'baseline_anxiety', 'age']
    for col in numeric_cols:
        if col in df.columns:
            # Use pd.to_numeric with errors='coerce' for vectorized conversion
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Vectorized missing value handling
    # Instead of iterating rows, use vectorized dropna
    # This is more efficient than row-wise apply
    if 'gender' in df.columns:
        # Vectorized string cleaning
        df['gender'] = df['gender'].astype(str).str.strip().str.lower()
    
    # Vectorized outlier handling (if needed)
    # Example: Cap values at 3 standard deviations (vectorized)
    for col in numeric_cols:
        if col in df.columns and df[col].notna().any():
            mean_val = df[col].mean()
            std_val = df[col].std()
            if std_val > 0:
                lower_bound = mean_val - 3 * std_val
                upper_bound = mean_val + 3 * std_val
                df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
    
    elapsed = time.time() - start_time
    logger.info(f"Vectorized cleaning completed in {elapsed:.2f}s")
    return df

def process_large_dataset_chunked(
    input_path: str,
    output_path: str,
    chunk_size: int = 1000
) -> Dict[str, Any]:
    """
    Process large datasets in chunks to avoid memory issues.
    
    Reads data in chunks, applies vectorized operations, and aggregates results.
    Designed to handle datasets that might not fit entirely in memory.
    """
    logger.info(f"Processing large dataset in chunks (chunk_size={chunk_size})...")
    start_time = time.time()
    
    config = load_config()
    ensure_directories()
    
    # Track statistics across chunks
    total_rows = 0
    processed_rows = 0
    chunks_processed = 0
    
    # Use chunked reading for large files
    chunks = []
    
    try:
        # Read in chunks if file is large
        chunk_iterator = pd.read_csv(input_path, chunksize=chunk_size)
        
        for i, chunk in enumerate(chunk_iterator):
            logger.debug(f"Processing chunk {i+1}")
            
            # Apply vectorized operations to each chunk
            chunk = vectorize_cleaning_operations(chunk)
            
            # Apply listwise deletion (vectorized internally)
            chunk = apply_listwise_deletion(chunk)
            
            chunks.append(chunk)
            total_rows += len(chunk)
            chunks_processed += 1
            
            # Log progress
            if (i + 1) % 5 == 0:
                logger.info(f"Processed {i+1} chunks, {total_rows} rows so far")
        
        if not chunks:
            logger.warning("No data chunks processed")
            # Create empty dataframe with expected schema
            df_result = pd.DataFrame(columns=[
                'news_exposure_freq', 'anxiety_score', 'baseline_anxiety', 'age', 'gender'
            ])
        else:
            # Concatenate all processed chunks
            logger.info(f"Concatenating {chunks_processed} chunks...")
            df_result = pd.concat(chunks, ignore_index=True)
        
        # Final validation
        df_result = vectorize_cleaning_operations(df_result)
        
        # Save result
        save_cleaned_data(df_result, output_path)
        
        elapsed = time.time() - start_time
        logger.info(f"Chunked processing completed in {elapsed:.2f}s")
        logger.info(f"Total rows processed: {len(df_result)}")
        
        return {
            'status': 'success',
            'total_rows': len(df_result),
            'chunks_processed': chunks_processed,
            'processing_time_seconds': elapsed,
            'output_path': output_path
        }
        
    except Exception as e:
        logger.error(f"Error during chunked processing: {str(e)}")
        raise

def benchmark_performance(input_path: str, target_records: int = 10000) -> Dict[str, Any]:
    """
    Benchmark performance on a dataset of specified size.
    
    Ensures processing time is under 60 seconds for target_records.
    """
    logger.info(f"Benchmarking performance on {target_records} records...")
    
    if not Path(input_path).exists():
        logger.error(f"Input file not found: {input_path}")
        return {'status': 'error', 'message': 'Input file not found'}
    
    # Load data
    df = pd.read_csv(input_path)
    
    # If dataset is smaller than target, simulate larger dataset
    if len(df) < target_records:
        logger.info(f"Dataset has {len(df)} records, replicating to {target_records}")
        n_replications = (target_records // len(df)) + 1
        df = pd.concat([df] * n_replications, ignore_index=True)
        df = df.iloc[:target_records]
    
    logger.info(f"Testing with {len(df)} records")
    
    # Measure processing time
    start_time = time.time()
    
    # Apply vectorized cleaning
    df_cleaned = vectorize_cleaning_operations(df)
    
    # Apply listwise deletion
    df_cleaned = apply_listwise_deletion(df_cleaned)
    
    elapsed = time.time() - start_time
    
    # Check if within target time
    within_target = elapsed < 60
    
    logger.info(f"Processing {len(df)} records took {elapsed:.2f}s")
    logger.info(f"Target: < 60s. Status: {'PASS' if within_target else 'FAIL'}")
    
    return {
        'status': 'success' if within_target else 'slow',
        'records_processed': len(df),
        'processing_time_seconds': elapsed,
        'target_time_seconds': 60,
        'within_target': within_target,
        'rows_after_cleaning': len(df_cleaned)
    }

def main():
    """Main entry point for performance optimization tasks."""
    config = load_config()
    ensure_directories()
    
    # Get paths
    raw_data_path = config.get('paths', {}).get('raw_data', 'data/raw/parsed_data.csv')
    processed_data_path = config.get('paths', {}).get('processed_data', 'data/processed/analysis_data.csv')
    
    logger.info("Starting performance optimization pipeline...")
    
    # Check if raw data exists, if not, try to download and parse
    if not Path(raw_data_path).exists():
        logger.info("Raw data not found. Attempting to download and parse...")
        try:
            # This would normally call download_data and parse_and_validate
            # For now, we assume the data exists from previous tasks
            logger.error("Raw data file not found. Please ensure T010a and T010b are completed.")
            return
        except Exception as e:
            logger.error(f"Failed to download/parse data: {e}")
            return
    
    # Benchmark performance
    benchmark_result = benchmark_performance(raw_data_path, target_records=10000)
    logger.info(f"Benchmark result: {benchmark_result}")
    
    # Process large dataset if needed
    if Path(raw_data_path).exists():
        try:
            result = process_large_dataset_chunked(raw_data_path, processed_data_path)
            logger.info(f"Chunked processing result: {result}")
        except PowerLimitationError as e:
            logger.error(f"Power limitation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error processing dataset: {e}")
            raise
    
    logger.info("Performance optimization pipeline completed.")

if __name__ == '__main__':
    main()
