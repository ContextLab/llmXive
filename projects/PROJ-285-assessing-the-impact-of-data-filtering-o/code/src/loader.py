"""
Chunked CSV/Parquet loader for the SLFC dataset.

Implements FR-001: Process large datasets without loading the full dataset into RAM.
Implements SC-005: Log peak memory usage and warn if > 6GB without failing.
"""
import os
import logging
import gc
import traceback
from pathlib import Path
from typing import Generator, Optional

import pandas as pd
import psutil

# Configure logging for the module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Constants
MAX_MEMORY_GB = 6.0
MAX_MEMORY_BYTES = MAX_MEMORY_GB * 1024**3
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MEMORY_PROFILE_PATH = PROJECT_ROOT / "data" / "processed" / "memory_profile.csv"

def _get_memory_usage_bytes() -> int:
    """Get current process memory usage in bytes."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss

def _log_memory_usage(step: str, current_bytes: int, peak_bytes: int):
    """Log memory usage and ensure directory exists for profile CSV."""
    current_gb = current_bytes / (1024**3)
    peak_gb = peak_bytes / (1024**3)
    
    logger.info(f"Memory Usage [{step}]: Current: {current_gb:.2f} GB, Peak: {peak_gb:.2f} GB")

    # Ensure output directory exists
    MEMORY_PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Append to memory profile
    import csv
    file_exists = MEMORY_PROFILE_PATH.exists() and MEMORY_PROFILE_PATH.stat().st_size > 0
    
    with open(MEMORY_PROFILE_PATH, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['step', 'current_gb', 'peak_gb'])
        writer.writerow([step, f"{current_gb:.4f}", f"{peak_gb:.4f}"])

    if current_bytes > MAX_MEMORY_BYTES:
        logger.warning(f"Memory usage ({current_gb:.2f} GB) exceeded threshold ({MAX_MEMORY_GB} GB). Continuing as per SC-005.")

def load_slfc_dataset_chunked(
    dataset_name: str = "astrovision/strong_lens_finding_challenge",
    chunk_size: int = 5000,
    columns: Optional[list] = None
) -> Generator[pd.DataFrame, None, None]:
    """
    Generator that yields chunks of the SLFC dataset.
    
    Args:
        dataset_name: HuggingFace dataset name.
        chunk_size: Number of rows to process at a time.
        columns: Optional list of columns to load. If None, loads all.
        
    Yields:
        pd.DataFrame: A chunk of the dataset.
    """
    logger.info(f"Starting chunked load of dataset: {dataset_name}")
    
    try:
        from datasets import load_dataset
        # Load the dataset in streaming mode to avoid initial RAM spike
        # Note: We use streaming to iterate without full download if possible, 
        # but for specific column access and chunking, we might need to batch.
        # Given the size constraints, we try to stream rows and accumulate chunks.
        
        ds = load_dataset(dataset_name, split="train", streaming=True)
        
        buffer = []
        peak_memory = 0
        chunk_count = 0

        for row in ds:
            buffer.append(row)
            
            if len(buffer) >= chunk_size:
                current_mem = _get_memory_usage_bytes()
                if current_mem > peak_memory:
                    peak_memory = current_mem
                
                chunk_df = pd.DataFrame(buffer)
                if columns:
                    # Filter columns if requested, dropping missing ones safely
                    existing_cols = [c for c in columns if c in chunk_df.columns]
                    chunk_df = chunk_df[existing_cols]
                
                chunk_count += 1
                _log_memory_usage(f"chunk_{chunk_count}", current_mem, peak_memory)
                
                yield chunk_df
                
                # Explicitly clear buffer to free memory
                buffer = []
                gc.collect()
        
        # Yield remaining rows if any
        if buffer:
            current_mem = _get_memory_usage_bytes()
            if current_mem > peak_memory:
                peak_memory = current_mem
            
            chunk_df = pd.DataFrame(buffer)
            if columns:
                existing_cols = [c for c in columns if c in chunk_df.columns]
                chunk_df = chunk_df[existing_cols]
            
            chunk_count += 1
            _log_memory_usage(f"chunk_{chunk_count}_final", current_mem, peak_memory)
            yield chunk_df

    except Exception as e:
        logger.error(f"Error loading dataset: {e}")
        logger.error(traceback.format_exc())
        raise

def process_slfc_dataset(
    dataset_name: str = "astrovision/strong_lens_finding_challenge",
    chunk_size: int = 5000,
    process_func=None
):
    """
    Main entry point to process the SLFC dataset in chunks.
    
    If process_func is provided, it is called on each chunk.
    If not, it simply iterates to ensure memory profiling happens.
    
    Args:
        dataset_name: HuggingFace dataset name.
        chunk_size: Rows per chunk.
        process_func: Optional function(chunk_df) -> None.
    """
    logger.info("Initializing SLFC dataset processing with chunked loader.")
    peak_memory = 0
    total_rows = 0

    for chunk in load_slfc_dataset_chunked(dataset_name, chunk_size):
        total_rows += len(chunk)
        current_mem = _get_memory_usage_bytes()
        if current_mem > peak_memory:
            peak_memory = current_mem
        
        if process_func:
            process_func(chunk)
        
        # Force garbage collection after processing each chunk
        gc.collect()

    _log_memory_usage("end_of_stream", peak_memory, peak_memory)
    logger.info(f"Processing complete. Total rows processed: {total_rows}. Peak Memory: {peak_memory / 1024**3:.2f} GB")
    
    if peak_memory > MAX_MEMORY_BYTES:
        logger.warning(f"Peak memory ({peak_memory / 1024**3:.2f} GB) exceeded 6GB limit.")

def main():
    """
    Main execution block to demonstrate the chunked loader and memory profiling.
    """
    # Ensure logging is configured for the script run
    logging.basicConfig(level=logging.INFO)
    
    logger.info("Running T005: Chunked SLFC Loader with Memory Profiling")
    
    try:
        # Process the dataset. 
        # We define a dummy process function that just counts rows to simulate work
        # without doing heavy computation that might skew memory measurements.
        def dummy_process(chunk):
            _ = len(chunk) 
            # If we needed to do something, we'd do it here.
            # For T005, the primary goal is loading and logging memory.
        
        process_slfc_dataset(
            dataset_name="astrovision/strong_lens_finding_challenge", 
            chunk_size=2000, 
            process_func=dummy_process
        )
        
        logger.info(f"Memory profile saved to: {MEMORY_PROFILE_PATH}")
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        raise

if __name__ == "__main__":
    main()
