"""
Chunked loading and subsampling for large fMRI datasets.

This module provides utilities to handle fMRI data that exceeds available RAM
by processing data in chunks and subsampling when necessary.

Implements:
- estimate_file_size_mb: Estimate file size in MB
- get_available_ram_gb: Get available system RAM
- calculate_chunk_size: Calculate optimal chunk size based on constraints
- load_fMRI_chunked: Load fMRI data in chunks
- subsample_fMRI: Subsample fMRI data to fit memory constraints
- iter_fMRI_chunks: Iterator for processing fMRI data in chunks
- process_roi_timecourses_chunked: Process ROI timecourses in chunks
- main: Entry point for standalone execution
"""
import os
import gc
import psutil
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Iterator, Dict, Any
from config import get_config
from utils.logging_config import get_logger, info, error, warning

logger = get_logger(__name__)

def estimate_file_size_mb(file_path: Path) -> float:
    """
    Estimate file size in megabytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File size in MB
        
    Raises:
        FileNotFoundError: If file does not exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    size_bytes = file_path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)
    logger.debug(f"Estimated file size for {file_path}: {size_mb:.2f} MB")
    return size_mb

def get_available_ram_gb() -> float:
    """
    Get available system RAM in gigabytes.
    
    Returns:
        Available RAM in GB
    """
    process = psutil.Process(os.getpid())
    available_memory = psutil.virtual_memory().available
    available_gb = available_memory / (1024 * 1024 * 1024)
    logger.debug(f"Available system RAM: {available_gb:.2f} GB")
    return available_gb

def calculate_chunk_size(
    file_size_mb: float,
    max_ram_gb: Optional[float] = None,
    safety_factor: float = 0.5
) -> int:
    """
    Calculate optimal chunk size for loading data.
    
    Args:
        file_size_mb: Size of the file in MB
        max_ram_gb: Maximum RAM to use (GB), defaults to config value
        safety_factor: Fraction of available RAM to use for chunking (0.0-1.0)
        
    Returns:
        Number of rows/chunks to load at once
    """
    config = get_config()
    if max_ram_gb is None:
        max_ram_gb = config.get('max_ram_gb', 7)
    
    available_gb = get_available_ram_gb()
    usable_gb = min(max_ram_gb, available_gb) * safety_factor
    
    # Convert to MB for calculation
    usable_mb = usable_gb * 1024
    
    # If file fits in memory, load it all
    if file_size_mb <= usable_mb:
        logger.info(f"File ({file_size_mb:.2f} MB) fits in available RAM ({usable_gb:.2f} GB). Loading entirely.")
        return -1  # Signal to load entire file
    
    # Calculate chunk size as a fraction of usable memory
    # Target: load 10-20 chunks at a time for efficient processing
    target_chunks = 15
    chunk_size_mb = usable_mb / target_chunks
    
    # Estimate rows per MB (rough heuristic: 1MB ≈ 1000 rows for typical fMRI data)
    # This is a simplification; actual rows depend on data structure
    rows_per_mb = 1000
    chunk_rows = int(chunk_size_mb * rows_per_mb)
    
    # Ensure minimum chunk size
    chunk_rows = max(chunk_rows, 100)
    
    logger.info(f"Calculated chunk size: {chunk_rows} rows (~{chunk_size_mb:.2f} MB)")
    return chunk_rows

def load_fMRI_chunked(
    file_path: Path,
    chunk_size: int = -1,
    dtype: np.dtype = np.float32,
    columns: Optional[list] = None
) -> np.ndarray:
    """
    Load fMRI data in chunks to handle large files.
    
    Args:
        file_path: Path to the data file (CSV or NPY)
        chunk_size: Number of rows per chunk, -1 for entire file
        dtype: Data type for the array
        columns: Specific columns to load (for CSV files)
        
    Returns:
        NumPy array containing the loaded data
        
    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If file format is unsupported
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    file_ext = file_path.suffix.lower()
    
    if file_ext == '.npy':
        # For .npy files, we still need to handle memory-mapped loading
        # if the file is too large
        if chunk_size == -1:
            logger.info(f"Loading entire .npy file: {file_path}")
            data = np.load(file_path, mmap_mode='r')
            return data.astype(dtype)
        else:
            # Memory-map and load in chunks
            logger.info(f"Loading .npy file in chunks: {file_path}")
            data = np.load(file_path, mmap_mode='r')
            total_rows = data.shape[0]
            result = []
            
            for start in range(0, total_rows, chunk_size):
                end = min(start + chunk_size, total_rows)
                chunk = np.array(data[start:end])
                result.append(chunk)
                gc.collect()
            
            return np.concatenate(result, axis=0).astype(dtype)
    
    elif file_ext == '.csv':
        import pandas as pd
        
        logger.info(f"Loading .csv file: {file_path}")
        
        if chunk_size == -1:
            # Load entire file
            df = pd.read_csv(file_path, dtype=dtype)
            if columns:
                df = df[columns]
            return df.values
        else:
            # Load in chunks
            chunks = []
            for chunk in pd.read_csv(file_path, chunksize=chunk_size, dtype=dtype):
                if columns:
                    chunk = chunk[columns]
                chunks.append(chunk.values)
                gc.collect()
            
            return np.concatenate(chunks, axis=0)
    
    else:
        raise ValueError(f"Unsupported file format: {file_ext}. Use .npy or .csv")

def subsample_fMRI(
    data: np.ndarray,
    target_size_mb: float,
    method: str = 'random'
) -> np.ndarray:
    """
    Subsample fMRI data to fit within memory constraints.
    
    Args:
        data: NumPy array of fMRI data
        target_size_mb: Target size in MB
        method: Subsampling method ('random', 'uniform', 'first')
        
    Returns:
        Subsampled NumPy array
        
    Raises:
        ValueError: If method is unsupported
    """
    if method not in ['random', 'uniform', 'first']:
        raise ValueError(f"Unsupported subsampling method: {method}")
    
    # Estimate current size
    current_size_mb = data.nbytes / (1024 * 1024)
    
    if current_size_mb <= target_size_mb:
        logger.info(f"Data ({current_size_mb:.2f} MB) already fits within target ({target_size_mb:.2f} MB)")
        return data
    
    # Calculate subsampling ratio
    ratio = target_size_mb / current_size_mb
    logger.info(f"Subsampling ratio: {ratio:.3f} (reducing from {current_size_mb:.2f} MB to {target_size_mb:.2f} MB)")
    
    if method == 'first':
        # Keep first N rows
        n_rows = max(1, int(data.shape[0] * ratio))
        return data[:n_rows]
    
    elif method == 'uniform':
        # Keep every Nth row
        step = max(1, int(1 / ratio))
        return data[::step]
    
    elif method == 'random':
        # Random sampling
        n_rows = max(1, int(data.shape[0] * ratio))
        indices = np.random.choice(data.shape[0], size=n_rows, replace=False)
        indices.sort()
        return data[indices]

def iter_fMRI_chunks(
    file_path: Path,
    chunk_size: int = 1000,
    dtype: np.dtype = np.float32,
    columns: Optional[list] = None
) -> Iterator[np.ndarray]:
    """
    Iterator for processing fMRI data in chunks.
    
    Args:
        file_path: Path to the data file
        chunk_size: Number of rows per chunk
        dtype: Data type for the array
        columns: Specific columns to load
        
    Yields:
        NumPy arrays containing chunk data
    """
    file_ext = file_path.suffix.lower()
    
    if file_ext == '.csv':
        import pandas as pd
        
        for chunk in pd.read_csv(file_path, chunksize=chunk_size, dtype=dtype):
            if columns:
                chunk = chunk[columns]
            yield chunk.values
            gc.collect()
    
    elif file_ext == '.npy':
        data = np.load(file_path, mmap_mode='r')
        total_rows = data.shape[0]
        
        for start in range(0, total_rows, chunk_size):
            end = min(start + chunk_size, total_rows)
            chunk = np.array(data[start:end])
            yield chunk
            gc.collect()
    
    else:
        raise ValueError(f"Unsupported file format: {file_ext}")

def process_roi_timecourses_chunked(
    input_path: Path,
    output_path: Path,
    chunk_size: Optional[int] = None,
    max_ram_gb: Optional[float] = None
) -> Dict[str, Any]:
    """
    Process ROI timecourses in chunks and save to output file.
    
    Args:
        input_path: Path to input file
        output_path: Path to output file
        chunk_size: Number of rows per chunk (auto-calculated if None)
        max_ram_gb: Maximum RAM to use (GB)
        
    Returns:
        Dictionary with processing statistics
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Estimate file size
    file_size_mb = estimate_file_size_mb(input_path)
    
    # Calculate chunk size if not provided
    if chunk_size is None:
        chunk_size = calculate_chunk_size(file_size_mb, max_ram_gb)
    
    stats = {
        'input_file': str(input_path),
        'output_file': str(output_path),
        'file_size_mb': file_size_mb,
        'chunk_size': chunk_size,
        'total_rows_processed': 0
    }
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if chunk_size == -1:
        # Load entire file
        logger.info("Loading entire file into memory")
        data = load_fMRI_chunked(input_path, chunk_size=-1)
        np.save(output_path, data)
        stats['total_rows_processed'] = data.shape[0]
        stats['output_shape'] = list(data.shape)
    else:
        # Process in chunks
        logger.info(f"Processing file in chunks of {chunk_size} rows")
        
        all_data = []
        for i, chunk in enumerate(iter_fMRI_chunks(input_path, chunk_size)):
            logger.debug(f"Processing chunk {i+1}: {chunk.shape}")
            all_data.append(chunk)
            stats['total_rows_processed'] += chunk.shape[0]
            gc.collect()
        
        # Concatenate and save
        result = np.concatenate(all_data, axis=0)
        np.save(output_path, result)
        stats['output_shape'] = list(result.shape)
    
    logger.info(f"Processing complete. Output saved to {output_path}")
    return stats

def main():
    """
    Main entry point for standalone execution.
    
    Demonstrates chunked loading and processing of fMRI data.
    """
    config = get_config()
    logger.info("Starting chunked loader demonstration")
    logger.info(f"Configuration: {config}")
    
    # Example usage with a hypothetical file
    # In practice, this would be called with real file paths
    input_file = Path("data/raw/example_fmri_data.csv")
    output_file = Path("data/processed/example_fmri_data_processed.npy")
    
    if input_file.exists():
        try:
            stats = process_roi_timecourses_chunked(
                input_file,
                output_file,
                max_ram_gb=config.get('max_ram_gb', 7)
            )
            logger.info(f"Processing statistics: {stats}")
        except Exception as e:
            error(f"Error processing file: {e}")
            raise
    else:
        logger.warning(f"Input file not found: {input_file}. Skipping demonstration.")
        logger.info("This script is designed to be imported and used by other pipeline components.")

if __name__ == "__main__":
    main()
