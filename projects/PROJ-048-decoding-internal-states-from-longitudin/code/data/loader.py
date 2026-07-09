import os
import sys
import logging
import h5py
import numpy as np
from pathlib import Path
from typing import Generator, Optional, Dict, Any, Tuple

try:
    from utils.logger import get_logger, log_stage_start, log_stage_end, log_error
    from utils.memory_monitor import check_memory_limit, MemoryExceededError, get_memory_limit_gb
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.logger import get_logger, log_stage_start, log_stage_end, log_error
    from utils.memory_monitor import check_memory_limit, MemoryExceededError, get_memory_limit_gb

class LoaderError(Exception):
    """Custom exception for loader failures."""
    pass

def get_file_size_mb(file_path: str) -> float:
    """Get file size in MB."""
    return os.path.getsize(file_path) / (1024 * 1024)

def load_chunked_hdf5(
    file_path: str,
    dataset_name: str,
    chunk_size: int = 1000,
    memory_limit_gb: Optional[float] = None
) -> Generator[np.ndarray, None, None]:
    """
    Load HDF5 data in chunks to ensure memory safety.
    
    Implements FR-001 and SC-001:
    - Intercepts dataset size checks.
    - Explicitly raises MemoryExceededError with message "Memory limit exceeded"
      if the dataset size exceeds the configured limit (default 5GB).
    
    Args:
        file_path: Path to the HDF5 file.
        dataset_name: Name of the dataset inside the HDF5 file.
        chunk_size: Number of rows to load per chunk.
        memory_limit_gb: Override for memory limit.
    
    Yields:
        NumPy arrays of shape (chunk_size, num_features).
    
    Raises:
        MemoryExceededError: If the dataset size exceeds the memory limit.
        LoaderError: If the file or dataset is not found.
    """
    logger = get_logger("loader")
    
    if not os.path.exists(file_path):
        raise LoaderError(f"File not found: {file_path}")
    
    # 1. Check File Size against Limit (FR-001, SC-001)
    limit = memory_limit_gb if memory_limit_gb is not None else get_memory_limit_gb()
    file_size_mb = get_file_size_mb(file_path)
    file_size_gb = file_size_mb / 1024.0
    
    logger.info(f"File size: {file_size_gb:.2f} GB (Limit: {limit} GB)")
    
    if file_size_gb > limit:
        raise MemoryExceededError("Memory limit exceeded")
    
    # 2. Open and Validate Dataset
    try:
        with h5py.File(file_path, 'r') as f:
            if dataset_name not in f:
                raise LoaderError(f"Dataset '{dataset_name}' not found in {file_path}")
            
            dset = f[dataset_name]
            total_rows = dset.shape[0]
            
            logger.info(f"Loading '{dataset_name}' with {total_rows} rows in chunks of {chunk_size}")
            
            # 3. Iterate in chunks
            for start in range(0, total_rows, chunk_size):
                end = min(start + chunk_size, total_rows)
                
                # Check memory before loading next chunk
                check_memory_limit()
                
                chunk = dset[start:end][:]
                yield chunk
                
    except h5py.HDF5Error as e:
        raise LoaderError(f"HDF5 error: {e}")

def load_full_with_check(file_path: str, dataset_name: str) -> np.ndarray:
    """
    Attempt to load the full dataset, but fail fast if it exceeds memory limits.
    
    Raises:
        MemoryExceededError: If the dataset exceeds the memory limit.
    """
    logger = get_logger("loader")
    limit = get_memory_limit_gb()
    
    file_size_mb = get_file_size_mb(file_path)
    file_size_gb = file_size_mb / 1024.0
    
    if file_size_gb > limit:
        raise MemoryExceededError("Memory limit exceeded")
    
    logger.info(f"Loading full dataset (safe size: {file_size_gb:.2f} GB)")
    
    with h5py.File(file_path, 'r') as f:
        if dataset_name not in f:
            raise LoaderError(f"Dataset '{dataset_name}' not found")
        return np.array(f[dataset_name])

def main():
    """Entry point for script execution."""
    import argparse
    parser = argparse.ArgumentParser(description="Load HDF5 Data with Memory Checks")
    parser.add_argument("--file", type=str, required=True, help="HDF5 file path")
    parser.add_argument("--dataset", type=str, required=True, help="Dataset name")
    parser.add_argument("--chunk-size", type=int, default=1000, help="Chunk size")
    args = parser.parse_args()
    
    try:
        logger = get_logger("loader")
        count = 0
        for chunk in load_chunked_hdf5(args.file, args.dataset, args.chunk_size):
            count += 1
            logger.debug(f"Loaded chunk {count}, shape: {chunk.shape}")
        logger.info(f"Successfully loaded {count} chunks.")
    except MemoryExceededError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except LoaderError as e:
        print(f"Loader Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
