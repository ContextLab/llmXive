"""
Batch processing and memory management utilities for the llmXive pipeline.

This module provides generators and context managers to process large datasets
in chunks, preventing memory overflow when handling large GitHub PR datasets.
"""
import os
import gc
import sys
import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Generator, Optional, Callable, Iterator
from contextlib import contextmanager

from utils.logging import get_logger, setup_logging
from utils.config import get_config_summary

logger = get_logger(__name__)

# Default chunk sizes
DEFAULT_CHUNK_SIZE = 100  # Number of records per chunk
MEMORY_THRESHOLD_MB = 500  # Trigger GC if memory usage exceeds this (approximate)

def get_memory_usage_mb() -> float:
    """
    Estimate current memory usage in MB.
    
    Returns:
        float: Estimated memory usage in MB.
    """
    try:
        import resource
        # Get memory usage of current process (in KB on Unix)
        mem_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return mem_kb / 1024.0
    except (ImportError, AttributeError):
        # Fallback for Windows or unavailable resource module
        return 0.0

def force_gc_if_needed(threshold_mb: int = MEMORY_THRESHOLD_MB) -> bool:
    """
    Force garbage collection if memory usage exceeds threshold.
    
    Args:
        threshold_mb: Memory threshold in MB.
        
    Returns:
        bool: True if GC was triggered, False otherwise.
    """
    current_mb = get_memory_usage_mb()
    if current_mb > threshold_mb:
        logger.debug(f"Memory usage {current_mb:.1f}MB exceeds threshold {threshold_mb}MB. Triggering GC.")
        gc.collect()
        return True
    return False

@contextmanager
def memory_monitor(threshold_mb: int = MEMORY_THRESHOLD_MB):
    """
    Context manager to monitor memory usage during processing.
    
    Yields:
        None
        
    Raises:
        MemoryError: If memory usage exceeds a critical limit (2x threshold).
    """
    start_mb = get_memory_usage_mb()
    logger.info(f"Memory monitoring started. Initial usage: {start_mb:.1f}MB")
    
    try:
        yield
    finally:
        end_mb = get_memory_usage_mb()
        delta_mb = end_mb - start_mb
        logger.info(f"Memory monitoring ended. Final usage: {end_mb:.1f}MB (Delta: {delta_mb:.1f}MB)")
        
        if end_mb > threshold_mb * 2:
            logger.warning(f"Critical memory usage: {end_mb:.1f}MB exceeds 2x threshold ({threshold_mb * 2}MB)")
            gc.collect()

def chunked_reader(file_path: Path, chunk_size: int = DEFAULT_CHUNK_SIZE) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Read a CSV file in chunks to handle large datasets efficiently.
    
    Args:
        file_path: Path to the CSV file.
        chunk_size: Number of rows per chunk.
        
    Yields:
        List of dictionaries representing rows in the chunk.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        chunk = []
        
        for row in reader:
            chunk.append(row)
            
            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []
                force_gc_if_needed()
                
        if chunk:
            yield chunk

def process_in_batches(
    input_path: Path,
    output_path: Path,
    processor_func: Callable[[Dict[str, Any]], Dict[str, Any]],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    append: bool = False
) -> int:
    """
    Process a CSV file in batches, applying a transformation function to each row.
    
    Args:
        input_path: Path to the input CSV file.
        output_path: Path to the output CSV file.
        processor_func: Function to apply to each row.
        chunk_size: Number of rows per batch.
        append: If True, append to existing output file; otherwise overwrite.
        
    Returns:
        int: Total number of rows processed.
    """
    total_rows = 0
    
    with memory_monitor():
        # Determine write mode
        write_mode = 'a' if append else 'w'
        header_written = append and output_path.exists()
        
        with open(output_path, write_mode, newline='', encoding='utf-8') as outfile:
            writer = None
            
            for i, chunk in enumerate(chunked_reader(input_path, chunk_size)):
                logger.info(f"Processing batch {i+1} ({len(chunk)} rows)...")
                
                processed_chunk = []
                for row in chunk:
                    try:
                        processed_row = processor_func(row)
                        processed_chunk.append(processed_row)
                    except Exception as e:
                        logger.error(f"Error processing row: {e}")
                        raise
                
                if not writer:
                    if processed_chunk:
                        fieldnames = list(processed_chunk[0].keys())
                        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                        if not header_written:
                            writer.writeheader()
                
                writer.writerows(processed_chunk)
                total_rows += len(processed_chunk)
                
                # Force GC after each batch
                force_gc_if_needed()
                
    logger.info(f"Batch processing complete. Total rows processed: {total_rows}")
    return total_rows

def load_json_batch(file_path: Path, key: Optional[str] = None) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Load a JSON file containing a list of records in batches.
    
    Args:
        file_path: Path to the JSON file.
        key: If the JSON is an object with a list under this key, extract that list.
             
    Yields:
        Lists of records in batches.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    if key and isinstance(data, dict):
        data = data.get(key, [])
        
    if not isinstance(data, list):
        raise ValueError(f"Expected a list in {file_path}, got {type(data)}")
        
    chunk = []
    for item in data:
        chunk.append(item)
        if len(chunk) >= DEFAULT_CHUNK_SIZE:
            yield chunk
            chunk = []
            force_gc_if_needed()
            
    if chunk:
        yield chunk

def save_batch_to_json(
    data_generator: Iterator[List[Dict[str, Any]]],
    output_path: Path,
    key: Optional[str] = None
) -> int:
    """
    Save a generator of batches to a JSON file efficiently.
    
    Args:
        data_generator: Generator yielding lists of records.
        output_path: Path to the output JSON file.
        key: Optional key to wrap the list under (e.g., {"results": [...]}).
        
    Returns:
        int: Total number of records saved.
    """
    total_count = 0
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        if key:
            f.write(f'{{"{key}": [')
        else:
            f.write('[')
            
        first_batch = True
        
        for i, batch in enumerate(data_generator):
            logger.info(f"Saving batch {i+1} ({len(batch)} records)...")
            
            if not first_batch:
                f.write(', ')
            first_batch = False
            
            # Write batch as JSON array elements
            for j, record in enumerate(batch):
                if j > 0:
                    f.write(', ')
                json.dump(record, f)
                total_count += 1
                
            force_gc_if_needed()
            
        if key:
            f.write(']}')
        else:
            f.write(']')
            
    logger.info(f"Saved {total_count} records to {output_path}")
    return total_count

def optimize_dataframe_memory(df) -> None:
    """
    Optimize memory usage of a pandas DataFrame by downcasting numeric types.
    
    Args:
        df: pandas DataFrame to optimize.
    """
    try:
        import pandas as pd
        
        for col in df.columns:
            col_type = df[col].dtype
            
            if col_type == 'object':
                # Convert to category if low cardinality
                if df[col].nunique() / len(df) < 0.5:
                    df[col] = df[col].astype('category')
            elif col_type.kind in ('i', 'u'):
                # Downcast integers
                c_min = df[col].min()
                c_max = df[col].max()
                if pd.api.types.is_signed_integer_dtype(col_type):
                    if c_min >= np.iinfo(np.int8).min and c_max <= np.iinfo(np.int8).max:
                        df[col] = df[col].astype(np.int8)
                    elif c_min >= np.iinfo(np.int16).min and c_max <= np.iinfo(np.int16).max:
                        df[col] = df[col].astype(np.int16)
                    elif c_min >= np.iinfo(np.int32).min and c_max <= np.iinfo(np.int32).max:
                        df[col] = df[col].astype(np.int32)
                else:
                    if c_min >= np.iinfo(np.uint8).min and c_max <= np.iinfo(np.uint8).max:
                        df[col] = df[col].astype(np.uint8)
                    elif c_min >= np.iinfo(np.uint16).min and c_max <= np.iinfo(np.uint16).max:
                        df[col] = df[col].astype(np.uint16)
                    elif c_min >= np.iinfo(np.uint32).min and c_max <= np.iinfo(np.uint32).max:
                        df[col] = df[col].astype(np.uint32)
            elif col_type.kind == 'f':
                # Downcast floats
                c_min = df[col].min()
                c_max = df[col].max()
                if c_min >= np.finfo(np.float32).min and c_max <= np.finfo(np.float32).max:
                    df[col] = df[col].astype(np.float32)
                
        logger.debug("DataFrame memory optimization complete")
    except ImportError:
        logger.warning("pandas not available, skipping DataFrame memory optimization")

def main():
    """
    Example usage of batch processing utilities.
    """
    setup_logging()
    logger.info("Batch processor utilities loaded successfully.")
    
    # Example: Process a large CSV file
    # input_file = Path("data/processed/large_dataset.csv")
    # output_file = Path("data/processed/processed_dataset.csv")
    # 
    # def my_processor(row):
    #     row['processed'] = True
    #     return row
    #
    # total = process_in_batches(input_file, output_file, my_processor)
    # print(f"Processed {total} rows")

if __name__ == "__main__":
    main()
