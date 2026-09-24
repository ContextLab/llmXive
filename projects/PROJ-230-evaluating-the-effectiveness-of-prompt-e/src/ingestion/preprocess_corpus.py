"""
Preprocess the downloaded corpus with memory-constrained streaming.

This module implements a dynamic chunking strategy to ensure the processed
dataset footprint remains <= 7GB RAM, adhering to SC-004. It uses the
`datasets` library in streaming mode to avoid loading the entire dataset
into memory at once.
"""
import os
import sys
import gc
import logging
import resource
import csv
import time
from pathlib import Path
from typing import Optional, Iterator, Dict, Any, List

# Import from local project structure
from src.ingestion.download_datasets import ensure_dirs
from src.utils.logging import get_logger

# Constants
MEMORY_LIMIT_GB = 7.0
MEMORY_LIMIT_BYTES = int(MEMORY_LIMIT_GB * 1024 * 1024 * 1024)
RAW_DATA_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
OUTPUT_CSV = PROCESSED_DIR / "corpus.csv"
LOG_FILE = PROCESSED_DIR / "preprocess_log.txt"

# Dynamic chunking parameters
INITIAL_CHUNK_SIZE = 100  # Start with a small chunk to estimate memory
MAX_CHUNK_SIZE = 10000    # Upper bound to prevent excessive memory spikes
MIN_CHUNK_SIZE = 10       # Lower bound

logger = get_logger(__name__)

def get_memory_usage_bytes() -> int:
    """Get current peak memory usage in bytes."""
    try:
        # Use resource module for Unix-like systems
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in kilobytes on Linux, but bytes on macOS
        # We normalize to bytes
        if sys.platform == 'darwin':
            return usage.ru_maxrss
        else:
            return usage.ru_maxrss * 1024
    except Exception:
        # Fallback to approximate if resource fails
        logger.warning("Could not get precise memory usage via resource module.")
        return 0

def get_memory_usage_gb() -> float:
    """Get current peak memory usage in GB."""
    return get_memory_usage_bytes() / (1024 * 1024 * 1024)

def check_memory_limit(current_usage_bytes: int) -> bool:
    """Check if current usage is within the 7GB limit."""
    return current_usage_bytes < MEMORY_LIMIT_BYTES

def load_raw_dataset_streaming(dataset_name: str, split: str = "train") -> Iterator[Dict[str, Any]]:
    """
    Load dataset in streaming mode to avoid memory overflow.
    
    Args:
        dataset_name: HuggingFace dataset name (e.g., 'codeparrot/code-trans-py-js')
        split: Dataset split to load (default: 'train')
        
    Returns:
        Iterator yielding rows from the dataset
    """
    try:
        from datasets import load_dataset
        logger.info(f"Loading dataset '{dataset_name}' in streaming mode...")
        dataset = load_dataset(dataset_name, split=split, streaming=True)
        logger.info("Dataset stream initialized successfully.")
        return iter(dataset)
    except Exception as e:
        logger.error(f"Failed to load dataset in streaming mode: {e}")
        raise

def process_chunk(chunk: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process a chunk of raw data: validate, clean, and transform.
    
    Args:
        chunk: List of raw dataset rows
        
    Returns:
        List of validated and processed rows
    """
    processed = []
    excluded_count = 0
    
    for i, row in enumerate(chunk):
        # Validate entry
        python_code = row.get("python_code", "")
        javascript_code = row.get("javascript_code", "")
        
        # Check for valid types and content
        if not isinstance(python_code, str) or not isinstance(javascript_code, str):
            excluded_count += 1
            continue
            
        if not python_code.strip() or not javascript_code.strip():
            excluded_count += 1
            continue
            
        # Basic length check to avoid extremely long entries
        if len(python_code) > 100000 or len(javascript_code) > 100000:
            excluded_count += 1
            continue
            
        processed.append({
            "python_code": python_code,
            "javascript_code": javascript_code,
            "id": f"row_{len(processed)}",
            "source": "streaming"
        })
    
    if excluded_count > 0:
        logger.warning(f"Excluded {excluded_count} invalid entries from chunk of size {len(chunk)}.")
        
    return processed

def process_buffer(buffer: List[Dict[str, Any]], writer: csv.DictWriter) -> int:
    """
    Write processed buffer to CSV and return number of rows written.
    
    Args:
        buffer: List of processed rows
        writer: CSV DictWriter instance
        
    Returns:
        Number of rows written
    """
    if not buffer:
        return 0
        
    writer.writerows(buffer)
    return len(buffer)

def process_and_save_corpus(
    dataset_name: str,
    chunk_size: int = INITIAL_CHUNK_SIZE,
    max_chunk_size: int = MAX_CHUNK_SIZE,
    min_chunk_size: int = MIN_CHUNK_SIZE
) -> Dict[str, Any]:
    """
    Main processing loop with dynamic chunk size adjustment.
    
    This function:
    1. Streams data from the dataset
    2. Processes chunks with adaptive size based on memory usage
    3. Writes results to CSV incrementally
    4. Logs memory usage and chunk size decisions
    
    Args:
        dataset_name: HuggingFace dataset name
        chunk_size: Initial chunk size
        max_chunk_size: Maximum allowed chunk size
        min_chunk_size: Minimum allowed chunk size
        
    Returns:
        Dictionary with statistics about the processing run
    """
    # Ensure output directories exist
    ensure_dirs()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialize CSV writer
    fieldnames = ["id", "python_code", "javascript_code", "source"]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        total_rows = 0
        total_excluded = 0
        chunk_sizes_used = []
        memory_samples = []
        current_chunk_size = chunk_size
        
        # Start streaming
        stream = load_raw_dataset_streaming(dataset_name)
        
        start_time = time.time()
        logger.info(f"Starting preprocessing with initial chunk size: {current_chunk_size}")
        
        buffer = []
        
        try:
            for row in stream:
                buffer.append(row)
                
                # Check if buffer is full or we've reached a memory limit
                if len(buffer) >= current_chunk_size:
                    # Process chunk
                    processed_chunk = process_chunk(buffer)
                    total_excluded += (len(buffer) - len(processed_chunk))
                    
                    # Write to CSV
                    rows_written = process_buffer(processed_chunk, writer)
                    total_rows += rows_written
                    
                    # Clear buffer
                    buffer = []
                    
                    # Check memory usage
                    current_memory = get_memory_usage_bytes()
                    memory_samples.append(current_memory)
                    
                    # Log memory usage
                    if len(memory_samples) % 10 == 0:  # Log every 10 chunks
                        logger.info(f"Processed {total_rows} rows. Peak memory: {get_memory_usage_gb():.2f} GB")
                    
                    # Adaptive chunk size logic
                    if current_memory > MEMORY_LIMIT_BYTES * 0.9:
                        # Memory is getting high, reduce chunk size
                        new_size = max(min_chunk_size, current_chunk_size // 2)
                        if new_size < current_chunk_size:
                            logger.warning(f"Memory usage high ({get_memory_usage_gb():.2f} GB). Reducing chunk size from {current_chunk_size} to {new_size}")
                            current_chunk_size = new_size
                    elif current_memory < MEMORY_LIMIT_BYTES * 0.5 and current_chunk_size < max_chunk_size:
                        # Memory is low, can increase chunk size
                        new_size = min(max_chunk_size, current_chunk_size * 2)
                        if new_size > current_chunk_size:
                            logger.info(f"Memory usage low ({get_memory_usage_gb():.2f} GB). Increasing chunk size from {current_chunk_size} to {new_size}")
                            current_chunk_size = new_size
                    
                    chunk_sizes_used.append(current_chunk_size)
                    
                    # Force garbage collection
                    gc.collect()
                    
        except KeyboardInterrupt:
            logger.warning("Processing interrupted by user. Writing partial results...")
        except Exception as e:
            logger.error(f"Error during processing: {e}")
            raise
        finally:
            # Write any remaining buffer
            if buffer:
                processed_chunk = process_chunk(buffer)
                rows_written = process_buffer(processed_chunk, writer)
                total_rows += rows_written
                total_excluded += (len(buffer) - len(processed_chunk))
                
            elapsed_time = time.time() - start_time
            
            # Final statistics
            stats = {
                "total_rows_processed": total_rows,
                "total_excluded": total_excluded,
                "final_chunk_size": current_chunk_size,
                "peak_memory_gb": max(memory_samples) / (1024 * 1024 * 1024) if memory_samples else 0,
                "average_chunk_size": sum(chunk_sizes_used) / len(chunk_sizes_used) if chunk_sizes_used else 0,
                "elapsed_time_seconds": elapsed_time
            }
            
            logger.info(f"Preprocessing complete. Stats: {stats}")
            
            # Log final memory usage
            final_memory = get_memory_usage_gb()
            logger.info(f"Final memory usage: {final_memory:.2f} GB")
            
            if final_memory > MEMORY_LIMIT_GB:
                logger.error(f"Memory limit exceeded! Final usage: {final_memory:.2f} GB > {MEMORY_LIMIT_GB} GB")
            else:
                logger.info(f"Memory constraint satisfied. Final usage: {final_memory:.2f} GB <= {MEMORY_LIMIT_GB} GB")
            
            return stats

def main():
    """Main entry point for preprocessing."""
    logger.info("Starting corpus preprocessing...")
    
    # Load from raw data directory if available, otherwise stream from HF
    # For this implementation, we stream directly to demonstrate the memory-constrained approach
    # In a real scenario, we might first check for cached data in data/raw/
    
    dataset_name = "codeparrot/code-trans-py-js"
    
    try:
        stats = process_and_save_corpus(dataset_name)
        
        # Validate output
        if stats["total_rows_processed"] < 200:
            logger.warning(f"Output corpus has only {stats['total_rows_processed']} rows. Expected >= 200.")
        else:
            logger.info(f"Output corpus has {stats['total_rows_processed']} rows. Requirement satisfied.")
            
        return 0
        
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())