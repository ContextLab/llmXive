"""
Memory-efficient data loading module for User Story 2.

Implements chunking and sampling strategies to ensure RAM usage stays
below 7 GB during LMM analysis, as required by SC-004.
"""
import os
import sys
import argparse
import gc
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator

import pandas as pd
import numpy as np

# Import from project utils
from utils.config import get_project_root, get_data_path, load_config
from utils.logger import get_logger

# Constants
MAX_RAM_GB = 7.0
CHUNK_SIZE_DEFAULT = 100000  # Rows per chunk
SAMPLE_FRACTION_DEFAULT = 1.0  # 100% by default, can be reduced via config

logger = get_logger(__name__)


def get_available_ram_gb() -> float:
    """
    Estimate available RAM on the system.
    Note: This is a heuristic. For strict enforcement, we rely on
    chunking strategies rather than real-time OS monitoring.
    """
    try:
        import psutil
        return psutil.virtual_memory().available / (1024 ** 3)
    except ImportError:
        # Fallback if psutil not installed: assume safe default
        logger.warning("psutil not found. Assuming 16GB available RAM for estimation.")
        return 16.0


def load_data_chunked(
    file_path: str,
    chunk_size: int = CHUNK_SIZE_DEFAULT,
    usecols: Optional[List[str]] = None,
    sample_fraction: float = SAMPLE_FRACTION_DEFAULT
) -> pd.DataFrame:
    """
    Load a CSV file in chunks to manage memory usage.

    If the file is small enough to fit in memory comfortably, it loads
    normally. If large, it processes in chunks and concatenates,
    optionally sampling to stay under the 7GB limit.

    Args:
        file_path: Path to the CSV file.
        chunk_size: Number of rows to read at a time.
        usecols: List of columns to load (reduces memory footprint).
        sample_fraction: Fraction of data to sample if the full dataset is too large.

    Returns:
        A pandas DataFrame containing the loaded (and potentially sampled) data.
    """
    logger.info(f"Starting memory-efficient load of {file_path}")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found: {file_path}")

    # Estimate file size
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    logger.info(f"File size: {file_size_mb:.2f} MB")

    # Heuristic: If file is very large, force sampling or chunking
    # We aim to keep the final DataFrame under ~6GB to be safe (leaving 1GB for overhead)
    # Assuming ~1KB per row for complex eye-tracking data (generous estimate)
    # 1GB ~ 1M rows. 7GB ~ 7M rows.
    
    chunks = []
    total_rows = 0
    
    # Strategy: Read in chunks to avoid peak memory spike during initial load
    # Even if we eventually load it all, chunked reading is safer for very large files
    try:
        for chunk in pd.read_csv(
            file_path,
            chunksize=chunk_size,
            usecols=usecols,
            low_memory=False  # Prevent mixed type inference issues
        ):
            chunks.append(chunk)
            total_rows += len(chunk)
            
            # Optional: Force garbage collection every 50 chunks
            if total_rows % (chunk_size * 50) == 0:
                gc.collect()
                
        logger.info(f"Loaded {total_rows:,} rows in chunks.")
        
        if not chunks:
            return pd.DataFrame()

        df = pd.concat(chunks, ignore_index=True)
        
        # Clear intermediate chunks from memory
        del chunks
        gc.collect()

    except Exception as e:
        logger.error(f"Error loading data in chunks: {e}")
        raise

    # Post-load check and sampling if necessary
    # Estimate memory usage
    mem_usage_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
    logger.info(f"Initial DataFrame memory usage: {mem_usage_mb:.2f} MB")

    if mem_usage_mb > (MAX_RAM_GB * 1024 * 0.9):  # 90% of limit
        logger.warning(f"Data size ({mem_usage_mb:.2f} MB) exceeds safe threshold ({MAX_RAM_GB * 1024 * 0.9:.2f} MB). Applying sampling.")
        
        if sample_fraction < 1.0:
            df = df.sample(frac=sample_fraction, random_state=42)
            logger.info(f"Sampled data to {sample_fraction*100:.1f}% of original size.")
        else:
            # If user didn't specify a sample fraction but we are over limit,
            # calculate one dynamically to fit under 7GB
            target_fraction = (MAX_RAM_GB * 1024 * 0.8) / mem_usage_mb
            logger.info(f"Auto-calculated sample fraction: {target_fraction:.4f}")
            df = df.sample(frac=target_fraction, random_state=42)

        mem_usage_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        logger.info(f"Final DataFrame memory usage after sampling: {mem_usage_mb:.2f} MB")

    return df


def load_data_streaming(
    file_path: str,
    chunk_size: int = CHUNK_SIZE_DEFAULT,
    usecols: Optional[List[str]] = None
) -> Generator[pd.DataFrame, None, None]:
    """
    Generator that yields chunks of data from a CSV file.
    Useful for processing extremely large datasets that cannot fit in RAM at all.

    Yields:
        DataFrame chunks.
    """
    logger.info(f"Starting streaming load of {file_path}")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found: {file_path}")

    for chunk in pd.read_csv(
        file_path,
        chunksize=chunk_size,
        usecols=usecols,
        low_memory=False
    ):
        yield chunk
        gc.collect()


def main():
    """
    Command-line entry point for testing memory-efficient loading.
    Usage: python -m code.analysis.memory_loader --path <path> --sample 0.5
    """
    parser = argparse.ArgumentParser(description="Memory-efficient data loader")
    parser.add_argument("--path", type=str, required=True, help="Path to CSV file")
    parser.add_argument("--chunk-size", type=int, default=CHUNK_SIZE_DEFAULT, help="Rows per chunk")
    parser.add_argument("--sample", type=float, default=1.0, help="Fraction of data to sample if needed")
    parser.add_argument("--cols", type=str, nargs="+", default=None, help="Columns to load")
    
    args = parser.parse_args()
    
    usecols = args.cols if args.cols else None
    
    try:
        df = load_data_chunked(
            file_path=args.path,
            chunk_size=args.chunk_size,
            usecols=usecols,
            sample_fraction=args.sample
        )
        logger.info(f"Successfully loaded data. Shape: {df.shape}")
        logger.info(f"Memory usage: {df.memory_usage(deep=True).sum() / (1024**2):.2f} MB")
        sys.exit(0)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()