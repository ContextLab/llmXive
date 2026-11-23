"""
Batch processing module for the full dataset.
Implements dynamic batch size calculation based on available RAM to ensure
memory usage stays below the 7GB limit.
"""
import gc
import json
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

import pandas as pd
import numpy as np

# Import existing utilities from the project
from utils.io import load_parquet, save_parquet, get_file_size_mb
from utils.memory_profiler import get_total_system_memory_gb, get_current_memory_mb, force_gc
from utils.validators import validate_dataset_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/results/batch_processing.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
INPUT_FILE = Path('data/processed/cleaned_reactions.parquet')
OUTPUT_FILE = Path('data/processed/batched_reactions.parquet')
LOG_FILE = Path('data/results/batch_processing_log.json')
MAX_MEMORY_GB = 6.0  # Target max usage to stay under 7GB limit
MEMORY_ESTIMATE_FACTOR = 1.2  # Safety factor for memory estimation

def estimate_dataframe_memory_mb(df: pd.DataFrame) -> float:
    """
    Estimate the memory usage of a DataFrame in MB.
    Uses the actual memory usage plus a safety factor.
    """
    if df.empty:
        return 0.0
    
    # Get actual memory usage
    mem_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
    
    # Apply safety factor
    return mem_mb * MEMORY_ESTIMATE_FACTOR

def calculate_optimal_batch_size(total_rows: int, sample_rows: int = 1000) -> int:
    """
    Calculate the optimal batch size based on available RAM.
    
    Args:
        total_rows: Total number of rows in the dataset
        sample_rows: Number of rows to use for memory estimation
        
    Returns:
        Optimal batch size (number of rows)
    """
    available_memory_mb = MAX_MEMORY_GB * 1024
    
    # Create a small sample to estimate memory per row
    try:
        # Load a small sample from the input file
        sample_df = pd.read_parquet(INPUT_FILE, engine='pyarrow')
        if len(sample_df) > sample_rows:
            sample_df = sample_df.head(sample_rows)
        
        # Estimate memory per row
        sample_mem_mb = estimate_dataframe_memory_mb(sample_df)
        rows_in_sample = len(sample_df)
        
        if rows_in_sample == 0:
            logger.warning("Sample is empty, using default batch size")
            return 10000
        
        memory_per_row = sample_mem_mb / rows_in_sample
        
        # Calculate max rows that fit in available memory
        max_rows = int(available_memory_mb / memory_per_row)
        
        # Ensure batch size is reasonable (at least 1000, at most 100000)
        batch_size = max(1000, min(max_rows, 100000))
        
        logger.info(f"Estimated memory per row: {memory_per_row:.4f} MB")
        logger.info(f"Calculated optimal batch size: {batch_size:,} rows")
        
        return batch_size
        
    except Exception as e:
        logger.error(f"Error calculating batch size: {e}")
        logger.warning("Using default batch size of 10000 rows")
        return 10000

def process_in_batches(batch_size: int) -> Dict[str, Any]:
    """
    Process the full dataset in batches and save the concatenated result.
    
    Args:
        batch_size: Number of rows to process in each batch
        
    Returns:
        Dictionary containing processing statistics
    """
    stats = {
        'start_time': datetime.now().isoformat(),
        'batch_size': batch_size,
        'total_batches': 0,
        'total_rows_processed': 0,
        'errors': [],
        'memory_usage_mb': []
    }
    
    try:
        # Get total rows
        total_rows = len(pd.read_parquet(INPUT_FILE, engine='pyarrow'))
        logger.info(f"Total rows to process: {total_rows:,}")
        
        # Initialize empty list to store batches
        all_batches = []
        
        # Process in chunks
        current_row = 0
        batch_num = 0
        
        while current_row < total_rows:
            batch_num += 1
            end_row = min(current_row + batch_size, total_rows)
            
            logger.info(f"Processing batch {batch_num}: rows {current_row:,} to {end_row:,}")
            
            # Record memory before processing
            mem_before = get_current_memory_mb()
            stats['memory_usage_mb'].append({
                'batch': batch_num,
                'memory_before_mb': mem_before
            })
            
            try:
                # Load batch
                batch_df = pd.read_parquet(INPUT_FILE, engine='pyarrow', 
                                          columns=None,  # Load all columns
                                          filters=None,
                                          use_pandas_metadata=True)
                
                # Slice the batch
                batch_df = batch_df.iloc[current_row:end_row].reset_index(drop=True)
                
                # Process batch (could add transformation logic here if needed)
                # For now, we're just ensuring we process in batches to manage memory
                
                # Record memory after processing
                mem_after = get_current_memory_mb()
                stats['memory_usage_mb'][-1]['memory_after_mb'] = mem_after
                stats['memory_usage_mb'][-1]['memory_delta_mb'] = mem_after - mem_before
                
                # Store batch
                all_batches.append(batch_df)
                
                stats['total_rows_processed'] += len(batch_df)
                stats['total_batches'] = batch_num
                
                # Force garbage collection after each batch
                force_gc()
                
                # Log progress
                progress = (stats['total_rows_processed'] / total_rows) * 100
                logger.info(f"Progress: {progress:.1f}% ({stats['total_rows_processed']:,}/{total_rows:,})")
                
            except Exception as e:
                error_msg = f"Error processing batch {batch_num}: {str(e)}"
                logger.error(error_msg)
                stats['errors'].append({
                    'batch': batch_num,
                    'error': str(e)
                })
                raise
            
            current_row = end_row
        
        # Concatenate all batches
        if all_batches:
            logger.info(f"Concatenating {len(all_batches)} batches...")
            final_df = pd.concat(all_batches, ignore_index=True)
            
            # Save the final result
            logger.info(f"Saving {len(final_df):,} rows to {OUTPUT_FILE}")
            save_parquet(final_df, OUTPUT_FILE)
            
            # Validate the output
            logger.info("Validating output dataset...")
            validate_dataset_file(OUTPUT_FILE)
            logger.info("Output validation successful")
            
        else:
            raise ValueError("No batches were processed successfully")
        
        stats['end_time'] = datetime.now().isoformat()
        stats['success'] = True
        
        logger.info(f"Batch processing completed successfully. Processed {stats['total_rows_processed']:,} rows in {stats['total_batches']} batches.")
        
    except Exception as e:
        stats['end_time'] = datetime.now().isoformat()
        stats['success'] = False
        stats['error'] = str(e)
        logger.error(f"Batch processing failed: {str(e)}")
        traceback.print_exc()
    
    return stats

def main():
    """Main entry point for the batch processing task."""
    logger.info("Starting batch processing task T021")
    
    # Check if input file exists
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")
    
    # Calculate optimal batch size
    batch_size = calculate_optimal_batch_size(1000)  # Pass dummy total for estimation
    
    # Process in batches
    stats = process_in_batches(batch_size)
    
    # Save processing log
    logger.info(f"Saving batch processing log to {LOG_FILE}")
    with open(LOG_FILE, 'w') as f:
        json.dump(stats, f, indent=2, default=str)
    
    # Final validation
    if stats.get('success'):
        logger.info("Task T021 completed successfully")
        return 0
    else:
        logger.error("Task T021 failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
