"""
Preprocess the downloaded dataset to ensure memory footprint <= 7GB RAM.

This module implements sampling and chunking logic to handle large datasets
without exceeding memory constraints. It reads from the raw cached dataset,
applies validation, and outputs a processed CSV file.

Dependencies:
- datasets (HuggingFace)
- pandas
- psutil (for memory monitoring)
"""
import os
import sys
import gc
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd
from datasets import Dataset
import psutil

# Import from project utils
from src.utils.logging import get_logger
from src.ingestion.validate_dataset import is_valid_entry, validate_and_filter_dataset

# Constants
MAX_MEMORY_GB = 7.0
MAX_MEMORY_BYTES = MAX_MEMORY_GB * (1024 ** 3)
CHUNK_SIZE = 5000  # Process in chunks of 5000 rows
OUTPUT_PATH = "data/processed/corpus.csv"
RAW_DATA_PATH = "data/raw"

logger = get_logger(__name__)

def get_memory_usage_bytes() -> float:
    """Get current memory usage in bytes."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss

def get_memory_usage_gb() -> float:
    """Get current memory usage in GB."""
    return get_memory_usage_bytes() / (1024 ** 3)

def check_memory_limit():
    """Check if we're approaching the memory limit and force GC if needed."""
    current_mem = get_memory_usage_gb()
    if current_mem > MAX_MEMORY_GB * 0.9:
        logger.warning(f"Memory usage at {current_mem:.2f}GB, approaching limit. Forcing GC...")
        gc.collect()
        return True
    return False

def load_raw_dataset_chunkwise(
    raw_data_dir: str,
    chunk_size: int = CHUNK_SIZE
) -> Dataset:
    """
    Load the raw dataset in chunks to monitor memory usage.
    
    Args:
        raw_data_dir: Path to directory containing raw dataset files
        chunk_size: Number of rows to process at once
        
    Returns:
        Dataset object with valid entries only
    """
    logger.info(f"Loading raw dataset from {raw_data_dir} with chunk size {chunk_size}")
    
    # Find all dataset files
    raw_files = list(Path(raw_data_dir).glob("*.csv")) + list(Path(raw_data_dir).glob("*.parquet"))
    
    if not raw_files:
        raise FileNotFoundError(f"No dataset files found in {raw_data_dir}")
    
    logger.info(f"Found {len(raw_files)} dataset files")
    
    all_valid_entries = []
    total_processed = 0
    total_valid = 0
    
    for file_path in raw_files:
        logger.info(f"Processing file: {file_path.name}")
        
        # Load dataset in chunks
        try:
            # Try to load as parquet first (more efficient), then csv
            if file_path.suffix == '.parquet':
                chunk_iter = pd.read_parquet(file_path, engine='pyarrow', chunksize=chunk_size)
            else:
                chunk_iter = pd.read_csv(file_path, chunksize=chunk_size)
            
            for chunk_idx, chunk in enumerate(chunk_iter):
                total_processed += len(chunk)
                
                # Check memory before processing chunk
                check_memory_limit()
                
                # Filter valid entries
                valid_mask = chunk.apply(
                    lambda row: is_valid_entry(row), axis=1
                )
                
                valid_chunk = chunk[valid_mask]
                total_valid += len(valid_chunk)
                
                # Add to results
                all_valid_entries.append(valid_chunk)
                
                # Log progress
                if chunk_idx % 10 == 0:
                    current_mem = get_memory_usage_gb()
                    logger.info(
                        f"  Chunk {chunk_idx}: Processed {total_processed} rows, "
                        f"Valid: {total_valid}, Memory: {current_mem:.2f}GB"
                    )
                    
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
            raise
    
    if not all_valid_entries:
        raise ValueError("No valid entries found in the dataset")
    
    # Combine all valid entries
    logger.info(f"Combining {len(all_valid_entries)} valid chunks")
    combined_df = pd.concat(all_valid_entries, ignore_index=True)
    
    # Convert to Dataset
    dataset = Dataset.from_pandas(combined_df)
    
    logger.info(f"Total valid entries: {len(dataset)}")
    logger.info(f"Final memory usage: {get_memory_usage_gb():.2f}GB")
    
    return dataset

def sample_dataset(
    dataset: Dataset,
    target_size_mb: Optional[float] = None,
    max_entries: Optional[int] = None
) -> Dataset:
    """
    Sample or truncate dataset to ensure it fits within memory constraints.
    
    Args:
        dataset: Input dataset
        target_size_mb: Target size in MB (default: estimate from memory)
        max_entries: Maximum number of entries to keep
        
    Returns:
        Sampled dataset
    """
    current_size = len(dataset)
    current_mem = get_memory_usage_gb()
    
    logger.info(f"Current dataset size: {current_size} entries, Memory: {current_mem:.2f}GB")
    
    # If no constraints specified, keep as is
    if target_size_mb is None and max_entries is None:
        logger.info("No sampling constraints specified, keeping full dataset")
        return dataset
    
    # Calculate max entries based on memory if not specified
    if max_entries is None and target_size_mb is not None:
        # Estimate average row size in bytes
        if current_size > 0:
            avg_row_size = (current_mem * (1024 ** 3)) / current_size
            max_entries = int((target_size_mb * (1024 ** 2)) / avg_row_size)
        else:
            max_entries = 1000000  # Default fallback
    
    # Sample if needed
    if max_entries is not None and current_size > max_entries:
        logger.info(f"Sampling dataset from {current_size} to {max_entries} entries")
        sampled_indices = dataset.sample(n=max_entries, random_state=42).indices
        dataset = dataset.select(sampled_indices)
        logger.info(f"Sampled dataset size: {len(dataset)} entries")
    
    return dataset

def process_and_save_corpus(
    raw_data_dir: str = RAW_DATA_PATH,
    output_path: str = OUTPUT_PATH,
    chunk_size: int = CHUNK_SIZE,
    target_size_mb: Optional[float] = None
) -> pd.DataFrame:
    """
    Main processing function that loads, validates, samples, and saves the corpus.
    
    Args:
        raw_data_dir: Path to raw data directory
        output_path: Path to save processed corpus
        chunk_size: Chunk size for processing
        target_size_mb: Target size in MB for sampling
        
    Returns:
        Processed DataFrame
    """
    logger.info("Starting corpus preprocessing")
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load raw dataset
    dataset = load_raw_dataset_chunkwise(raw_data_dir, chunk_size)
    
    # Apply sampling if needed
    dataset = sample_dataset(dataset, target_size_mb)
    
    # Convert to DataFrame
    df = dataset.to_pandas()
    
    # Ensure required columns exist
    required_cols = ['python_code', 'javascript_code']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Final validation
    logger.info(f"Performing final validation on {len(df)} entries")
    valid_mask = df.apply(lambda row: is_valid_entry(row), axis=1)
    df = df[valid_mask].reset_index(drop=True)
    
    logger.info(f"Final valid entries: {len(df)}")
    
    # Save to CSV
    logger.info(f"Saving processed corpus to {output_path}")
    df.to_csv(output_path, index=False)
    
    # Log final statistics
    final_mem = get_memory_usage_gb()
    logger.info(f"Processing complete. Final memory usage: {final_mem:.2f}GB")
    logger.info(f"Output file size: {Path(output_path).stat().st_size / (1024**2):.2f}MB")
    
    return df

def main():
    """Main entry point for the preprocessing script."""
    logger.info("Starting preprocess_corpus.py")
    
    try:
        df = process_and_save_corpus()
        
        logger.info(f"Successfully processed {len(df)} entries")
        logger.info(f"Output saved to {OUTPUT_PATH}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error during preprocessing: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())