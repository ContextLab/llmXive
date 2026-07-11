"""
Memory-efficient data loading utilities for the visual attention pipeline.

Implements chunked and streaming loading strategies to ensure RAM usage
stays below the 7GB threshold (SC-004).
"""
import os
import sys
import argparse
import gc
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator

import pandas as pd
import psutil

# Import project utilities
try:
    from utils.logger import get_logger
    from utils.config import get_project_root, get_data_path
except ImportError:
    # Fallback for direct execution or different import context
    import logging
    def get_logger(name):
        return logging.getLogger(name)

logger = get_logger(__name__)

def get_available_ram_gb() -> float:
    """
    Returns the available RAM in GB on the current system.
    """
    try:
        mem = psutil.virtual_memory()
        return mem.available / (1024 ** 3)
    except Exception as e:
        logger.warning(f"Could not determine available RAM: {e}. Defaulting to 4GB.")
        return 4.0

def load_data_chunked(
    file_path: str,
    chunk_size: int = 10000,
    usecols: Optional[List[str]] = None,
    dtype: Optional[Dict[str, Any]] = None
) -> Generator[pd.DataFrame, None, None]:
    """
    Loads a CSV file in chunks to minimize memory footprint.
    
    Args:
        file_path: Path to the CSV file.
        chunk_size: Number of rows per chunk.
        usecols: Optional list of columns to load.
        dtype: Optional dictionary of column data types.
        
    Yields:
        DataFrames containing chunks of the data.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    logger.info(f"Loading {file_path} in chunks of {chunk_size} rows...")
    
    # Determine total rows for progress if possible (optional optimization)
    try:
        # Attempt to estimate size or just iterate
        for chunk in pd.read_csv(
            file_path,
            chunksize=chunk_size,
            usecols=usecols,
            dtype=dtype,
            low_memory=True
        ):
            yield chunk
            # Explicitly trigger garbage collection periodically if chunks are large
            # This helps prevent fragmentation in long-running streams
            gc.collect()
    except Exception as e:
        logger.error(f"Error reading chunked data from {file_path}: {e}")
        raise

def load_data_streaming(
    file_path: str,
    target_ram_gb: float = 6.0,
    usecols: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Loads data into memory using a dynamic sampling strategy to stay within
    the target RAM limit (SC-004).
    
    If the full dataset fits in RAM, it is loaded. If not, a representative
    sample is taken to ensure memory usage remains safe.
    
    Args:
        file_path: Path to the CSV file.
        target_ram_gb: Maximum RAM to target for the loaded DataFrame (default 6GB).
        usecols: Optional list of columns to load.
        
    Returns:
        A DataFrame either containing the full data or a sample.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    logger.info(f"Analyzing memory requirements for {file_path}...")
    
    # Estimate memory usage by reading a small sample first
    sample_size = 1000
    try:
        sample_df = pd.read_csv(file_path, nrows=sample_size, usecols=usecols)
    except Exception as e:
        logger.error(f"Failed to read sample for size estimation: {e}")
        raise
    
    # Estimate size per row in bytes
    sample_size_bytes = sample_df.memory_usage(deep=True).sum()
    bytes_per_row = sample_size_bytes / sample_size
    
    # Estimate total rows (approximate)
    # We can't easily get total rows without reading, so we assume a large number
    # and check if the estimated full size exceeds target.
    # A safer approach for unknown large files: try loading, catch MemoryError,
    # or estimate file size on disk.
    
    file_size_bytes = os.path.getsize(file_path)
    # Rough estimate: CSV is often 1.2x-1.5x the RAM size of the parsed DataFrame
    # due to string overhead, etc. Let's be conservative.
    estimated_ram_bytes = file_size_bytes * 1.5 
    
    available_ram_bytes = get_available_ram_gb() * (1024 ** 3)
    safe_limit_bytes = target_ram_gb * (1024 ** 3)
    
    # Calculate max safe rows
    if bytes_per_row > 0:
        max_safe_rows = int(safe_limit_bytes / bytes_per_row)
    else:
        max_safe_rows = float('inf')
        
    total_rows_estimate = file_size_bytes / (bytes_per_row + 1) # +1 for newline overhead approx
    
    logger.info(f"Estimated file size: {file_size_bytes / (1024**2):.2f} MB")
    logger.info(f"Estimated RAM usage for full load: {estimated_ram_bytes / (1024**3):.2f} GB")
    logger.info(f"Target RAM limit: {target_ram_gb} GB")
    logger.info(f"Available system RAM: {get_available_ram_gb():.2f} GB")
    
    if estimated_ram_bytes <= safe_limit_bytes:
        logger.info("Full dataset fits within safe memory limits. Loading all data.")
        df = pd.read_csv(file_path, usecols=usecols)
        # Force garbage collection after load
        gc.collect()
        return df
    else:
        logger.warning("Full dataset exceeds safe memory limits. Sampling data.")
        # Calculate sample fraction to stay within limit
        sample_fraction = safe_limit_bytes / estimated_ram_bytes
        # Ensure we don't sample too little (at least 1000 rows if possible)
        if total_rows_estimate * sample_fraction < 1000:
            sample_fraction = 1000 / total_rows_estimate if total_rows_estimate > 0 else 1.0
        
        logger.info(f"Sampling fraction: {sample_fraction:.4f}")
        df = pd.read_csv(file_path, usecols=usecols, sample=sample_fraction)
        gc.collect()
        logger.info(f"Loaded {len(df)} rows. Estimated RAM usage: {df.memory_usage(deep=True).sum() / (1024**3):.3f} GB")
        return df

def main():
    """
    CLI entry point for memory loader tests/demos.
    Usage: python code/analysis/memory_loader.py --file <path>
    """
    parser = argparse.ArgumentParser(description="Memory Efficient Data Loader")
    parser.add_argument("--file", type=str, required=True, help="Path to CSV file")
    parser.add_argument("--chunk-size", type=int, default=5000, help="Chunk size for chunked loading")
    parser.add_argument("--target-ram", type=float, default=6.0, help="Target RAM in GB")
    args = parser.parse_args()
    
    project_root = get_project_root()
    if not os.path.isabs(args.file):
        data_path = get_data_path()
        file_path = os.path.join(data_path, args.file)
    else:
        file_path = args.file
        
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        sys.exit(1)
        
    print(f"System Available RAM: {get_available_ram_gb():.2f} GB")
    
    # Test streaming load
    try:
        df = load_data_streaming(file_path, target_ram_gb=args.target_ram)
        print(f"Success. Loaded {len(df)} rows.")
        print(df.head())
        sys.exit(0)
    except Exception as e:
        print(f"Streaming load failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
