"""
Chunked loader for the SLFC dataset.
Processes the dataset in chunks to avoid loading the full dataset into RAM.
Logs peak memory usage to data/processed/memory_profile.csv.
"""
import os
import logging
import gc
import traceback
import psutil
import time
from pathlib import Path
from typing import Generator, Optional, List, Dict, Any
import pandas as pd

# Import existing utilities from the project
from src.logging_config import get_logger, configure_logging, get_log_file_path

# Configure logging
logger = get_logger(__name__)

# Constants
MEMORY_LIMIT_GB = 6.0
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_GB * 1024 ** 3
OUTPUT_DIR = Path("data/processed")
MEMORY_PROFILE_FILE = OUTPUT_DIR / "memory_profile.csv"

def get_memory_usage_bytes() -> int:
    """Get current memory usage of the current process in bytes."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss

def format_memory_bytes(bytes_val: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} TB"

def load_slfc_dataset_chunked(
    dataset_name: str = "kylehston/strong_lens_finding_challenge",
    split: str = "train",
    chunk_size: int = 10000,
    streaming: bool = True
) -> Generator[pd.DataFrame, None, None]:
    """
    Load the SLFC dataset in chunks to avoid memory overload.
    
    Args:
        dataset_name: HuggingFace dataset name
        split: Dataset split to load
        chunk_size: Number of rows per chunk
        streaming: Whether to use streaming mode (True for large datasets)
        
    Yields:
        pd.DataFrame: Chunk of the dataset
    """
    from datasets import load_dataset
    
    logger.info(f"Loading dataset '{dataset_name}' split '{split}' in chunked mode...")
    
    try:
        if streaming:
            # Use streaming to avoid downloading the full dataset
            dataset = load_dataset(dataset_name, split=split, streaming=True)
            
            # Convert to pandas in chunks
            buffer = []
            for idx, item in enumerate(dataset):
                buffer.append(item)
                if len(buffer) >= chunk_size:
                    yield pd.DataFrame(buffer)
                    buffer = []
                    gc.collect()
                    
            # Yield remaining items
            if buffer:
                yield pd.DataFrame(buffer)
        else:
            # Non-streaming mode (load all into memory - not recommended for large datasets)
            dataset = load_dataset(dataset_name, split=split)
            num_rows = len(dataset)
            for start_idx in range(0, num_rows, chunk_size):
                end_idx = min(start_idx + chunk_size, num_rows)
                chunk_df = dataset.select(range(start_idx, end_idx)).to_pandas()
                yield chunk_df
                gc.collect()
                
    except Exception as e:
        logger.error(f"Error loading dataset: {e}")
        raise

def process_slfc_dataset(
    dataset_name: str = "kylehston/strong_lens_finding_challenge",
    split: str = "train",
    chunk_size: int = 10000,
    process_func: Optional[callable] = None
) -> Dict[str, Any]:
    """
    Process the SLFC dataset in chunks and track memory usage.
    
    Args:
        dataset_name: HuggingFace dataset name
        split: Dataset split to load
        chunk_size: Number of rows per chunk
        process_func: Optional function to apply to each chunk
        
    Returns:
        Dict with processing statistics including peak memory usage
    """
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialize memory tracking
    peak_memory_bytes = 0
    memory_samples = []
    start_time = time.time()
    total_rows_processed = 0
    
    logger.info(f"Starting chunked processing of '{dataset_name}' split '{split}'")
    logger.info(f"Memory limit: {format_memory_bytes(MEMORY_LIMIT_BYTES)}")
    
    try:
        for chunk_idx, chunk_df in enumerate(load_slfc_dataset_chunked(
            dataset_name=dataset_name,
            split=split,
            chunk_size=chunk_size
        )):
            # Process the chunk if a function is provided
            if process_func:
                chunk_df = process_func(chunk_df)
            
            # Track memory usage
            current_memory = get_memory_usage_bytes()
            if current_memory > peak_memory_bytes:
                peak_memory_bytes = current_memory
            
            memory_samples.append({
                'chunk_id': chunk_idx,
                'timestamp': time.time(),
                'memory_bytes': current_memory,
                'memory_gb': current_memory / (1024 ** 3),
                'rows_in_chunk': len(chunk_df)
            })
            
            total_rows_processed += len(chunk_df)
            
            # Log progress
            if (chunk_idx + 1) % 10 == 0:
                logger.info(f"Processed {chunk_idx + 1} chunks ({total_rows_processed} rows)")
                logger.info(f"Current memory: {format_memory_bytes(current_memory)}")
            
            # Check memory limit and log warning if exceeded
            if current_memory > MEMORY_LIMIT_BYTES:
                logger.warning(
                    f"Memory usage {format_memory_bytes(current_memory)} exceeds limit "
                    f"({format_memory_bytes(MEMORY_LIMIT_BYTES)})"
                )
            
            # Force garbage collection
            gc.collect()
            
    except Exception as e:
        logger.error(f"Error during processing: {e}")
        traceback.print_exc()
        raise
    
    end_time = time.time()
    processing_time_seconds = end_time - start_time
    
    # Log final statistics
    logger.info(f"Processing complete!")
    logger.info(f"Total rows processed: {total_rows_processed}")
    logger.info(f"Peak memory usage: {format_memory_bytes(peak_memory_bytes)}")
    logger.info(f"Processing time: {processing_time_seconds:.2f} seconds")
    
    # Check if peak memory exceeded limit
    if peak_memory_bytes > MEMORY_LIMIT_BYTES:
        logger.warning(
            f"Peak memory usage {format_memory_bytes(peak_memory_bytes)} exceeded "
            f"the {MEMORY_LIMIT_GB}GB limit (SC-005)"
        )
    
    # Save memory profile to CSV
    if memory_samples:
        memory_df = pd.DataFrame(memory_samples)
        memory_df.to_csv(MEMORY_PROFILE_FILE, index=False)
        logger.info(f"Memory profile saved to: {MEMORY_PROFILE_FILE}")
    
    return {
        'total_rows': total_rows_processed,
        'peak_memory_bytes': peak_memory_bytes,
        'peak_memory_gb': peak_memory_bytes / (1024 ** 3),
        'processing_time_seconds': processing_time_seconds,
        'memory_limit_exceeded': peak_memory_bytes > MEMORY_LIMIT_BYTES,
        'memory_profile_path': str(MEMORY_PROFILE_FILE)
    }

def main():
    """Main entry point for chunked dataset processing."""
    logger.info("Starting SLFC dataset chunked processing...")
    
    try:
        # Process the dataset
        results = process_slfc_dataset(
            dataset_name="kylehston/strong_lens_finding_challenge",
            split="train",
            chunk_size=10000
        )
        
        logger.info("Chunked processing completed successfully!")
        logger.info(f"Results: {results}")
        
    except Exception as e:
        logger.error(f"Failed to process dataset: {e}")
        raise

if __name__ == "__main__":
    # Configure logging
    configure_logging()
    
    # Run main
    main()
