"""
Chunked loading module for handling large fMRI datasets (>7GB) that exceed RAM constraints.
Implements streaming chunk processing, memory-aware sizing, and subsampling strategies.
"""
import os
import gc
import psutil
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Iterator, Dict, Any

from config import get_config
from utils.logging_config import get_logger, info, error, warning

def estimate_file_size_mb(file_path: str) -> float:
    """
    Estimates the size of a file in megabytes.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Size in MB.
    """
    size_bytes = os.path.getsize(file_path)
    return size_bytes / (1024 * 1024)

def get_available_ram_gb() -> float:
    """
    Returns the available RAM in gigabytes.
    
    Returns:
        Available RAM in GB.
    """
    mem = psutil.virtual_memory()
    return mem.available / (1024 ** 3)

def calculate_chunk_size(file_size_mb: float, max_ram_gb: float, safety_factor: float = 0.5) -> int:
    """
    Calculates an appropriate chunk size to process a file without exceeding RAM limits.
    
    Args:
        file_size_mb: Total file size in MB.
        max_ram_gb: Maximum RAM available in GB.
        safety_factor: Fraction of RAM to use for processing (default 0.5).
        
    Returns:
        Number of timepoints (rows) per chunk.
    """
    # Assume float64 data (8 bytes per value)
    # Estimate rows: file_size_mb * 1024 * 1024 / (num_cols * 8)
    # For simplicity, assume a typical fMRI timecourse has ~100-500 timepoints per subject
    # and multiple ROIs. We'll estimate based on a conservative row size.
    # Let's assume 1000 columns (features) per row for a worst-case scenario.
    estimated_row_size_bytes = 1000 * 8  # 1000 float64 values
    
    max_bytes_to_use = (max_ram_gb * (1024 ** 3)) * safety_factor
    chunk_rows = int(max_bytes_to_use / estimated_row_size_bytes)
    
    # Ensure chunk size is at least 100 rows
    return max(chunk_rows, 100)

def load_fMRI_chunked(
    file_path: str,
    chunk_size: Optional[int] = None,
    max_ram_gb: Optional[float] = None
) -> Iterator[np.ndarray]:
    """
    Loads a large fMRI data file (NIfTI or NPY) in chunks to avoid OOM errors.
    
    Args:
        file_path: Path to the input file (.nii, .nii.gz, or .npy).
        chunk_size: Number of rows (timepoints) to load per chunk. If None, calculated automatically.
        max_ram_gb: Maximum RAM to use in GB. If None, uses config or available RAM.
        
    Yields:
        np.ndarray chunks of shape (chunk_size, num_features).
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is unsupported.
    """
    logger = get_logger(__name__)
    
    path = Path(file_path)
    if not path.exists():
        error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Determine max RAM
    if max_ram_gb is None:
        config = get_config()
        max_ram_gb = config.get('max_ram_gb', 7)
    
    # Estimate file size and calculate chunk size
    file_size_mb = estimate_file_size_mb(str(path))
    if file_size_mb < 100:  # Small file, load entirely
        logger.info(f"File {file_path} is small ({file_size_mb:.2f} MB), loading entirely.")
        if path.suffix == '.npy':
            data = np.load(str(path))
            yield data
            return
        elif path.suffix in ['.nii', '.nii.gz']:
            import nibabel as nib
            img = nib.load(str(path))
            data = img.get_fdata()
            # Reshape to 2D if necessary (timepoints x voxels)
            if data.ndim > 2:
                data = data.reshape(-1, data.shape[-1])
            yield data
            return
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
    
    # Large file, calculate chunk size
    if chunk_size is None:
        chunk_size = calculate_chunk_size(file_size_mb, max_ram_gb)
    
    logger.info(f"Processing {file_path} in chunks of {chunk_size} rows.")
    
    if path.suffix == '.npy':
        # For .npy files, we can memory map
        mmapped = np.load(str(path), mmap_mode='r')
        total_rows = mmapped.shape[0]
        
        for start in range(0, total_rows, chunk_size):
            end = min(start + chunk_size, total_rows)
            chunk = mmapped[start:end]
            # Ensure we get a copy if needed for processing
            yield np.array(chunk)
            del chunk
            gc.collect()
            
    elif path.suffix in ['.nii', '.nii.gz']:
        import nibabel as nib
        
        # Load image
        img = nib.load(str(path))
        data = img.get_fdata()
        
        # Determine how to chunk (assume last dimension is time or we reshape)
        # If 4D (x, y, z, t), we might want to chunk over time
        # If 2D (time, voxels), chunk over time
        if data.ndim == 4:
            # Reshape to (time, voxels) for chunking
            x, y, z, t = data.shape
            data_2d = data.reshape(-1, t).T  # (t, x*y*z)
            total_rows = t
            for start in range(0, total_rows, chunk_size):
                end = min(start + chunk_size, total_rows)
                chunk = data_2d[start:end]
                yield chunk
                del chunk
                gc.collect()
        elif data.ndim == 3:
            # Static volume, no chunking needed over time
            yield data.reshape(1, -1)
        else:
            # Flatten and chunk
            data_flat = data.reshape(-1, 1)
            total_rows = data_flat.shape[0]
            for start in range(0, total_rows, chunk_size):
                end = min(start + chunk_size, total_rows)
                yield data_flat[start:end]
                gc.collect()
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")

def subsample_fMRI(
    data: np.ndarray,
    subsample_rate: float = 1.0,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Subsamples an fMRI dataset to reduce size for testing or quick processing.
    
    Args:
        data: Input data array.
        subsample_rate: Fraction of data to keep (0.0 to 1.0).
        seed: Random seed for reproducibility.
        
    Returns:
        Subsampled data array.
    """
    if subsample_rate >= 1.0:
        return data
    
    if seed is not None:
        np.random.seed(seed)
    
    n_rows = data.shape[0]
    n_keep = int(n_rows * subsample_rate)
    indices = np.random.choice(n_rows, size=n_keep, replace=False)
    indices.sort()
    
    return data[indices]

def iter_fMRI_chunks(
    file_path: str,
    chunk_size: Optional[int] = None,
    max_ram_gb: Optional[float] = None,
    subsample_rate: float = 1.0,
    seed: Optional[int] = None
) -> Iterator[np.ndarray]:
    """
    Iterates over chunks of an fMRI file, with optional subsampling.
    
    Args:
        file_path: Path to the input file.
        chunk_size: Rows per chunk.
        max_ram_gb: Max RAM to use.
        subsample_rate: Fraction of each chunk to keep.
        seed: Random seed for subsampling.
        
    Yields:
        Subsampled numpy chunks.
    """
    for chunk in load_fMRI_chunked(file_path, chunk_size, max_ram_gb):
        if subsample_rate < 1.0:
            chunk = subsample_fMRI(chunk, subsample_rate, seed)
        yield chunk

def process_roi_timecourses_chunked(
    input_file: str,
    output_file: str,
    chunk_size: Optional[int] = None,
    max_ram_gb: Optional[float] = None,
    aggregation_func: str = 'mean'
) -> None:
    """
    Processes ROI timecourses in chunks and writes aggregated results to output.
    
    Args:
        input_file: Path to input fMRI data file.
        output_file: Path to output CSV or NPY file.
        chunk_size: Rows per chunk.
        max_ram_gb: Max RAM to use.
        aggregation_func: Aggregation function ('mean', 'sum', 'max', 'min').
    """
    logger = get_logger(__name__)
    info(f"Processing {input_file} to {output_file} in chunks.")
    
    agg_funcs = {
        'mean': np.mean,
        'sum': np.sum,
        'max': np.max,
        'min': np.min
    }
    
    if aggregation_func not in agg_funcs:
        raise ValueError(f"Unsupported aggregation function: {aggregation_func}")
    
    agg = agg_funcs[aggregation_func]
    
    results = []
    
    for i, chunk in enumerate(iter_fMRI_chunks(input_file, chunk_size, max_ram_gb)):
        logger.info(f"Processing chunk {i+1}, shape: {chunk.shape}")
        aggregated = agg(chunk, axis=0)
        results.append(aggregated)
        
        # Periodic garbage collection
        if i % 10 == 0:
            gc.collect()
    
    if not results:
        error("No data was processed.")
        raise ValueError("No data was processed.")
    
    # Combine results
    final_result = np.vstack(results)
    
    # Save output
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if output_file.endswith('.npy'):
        np.save(str(output_path), final_result)
    elif output_file.endswith('.csv'):
        import pandas as pd
        df = pd.DataFrame(final_result)
        df.to_csv(str(output_path), index=False)
    else:
        raise ValueError(f"Unsupported output format: {output_file}")
    
    info(f"Successfully saved aggregated results to {output_file}")

def main() -> None:
    """
    Main entry point for testing chunked loading.
    This function is intended for manual testing and demonstration.
    """
    config = get_config()
    logger = get_logger(__name__)
    
    # Example usage:
    # 1. Estimate file size
    # 2. Calculate chunk size
    # 3. Iterate and process
    
    logger.info("Chunked loader module loaded successfully.")
    logger.info(f"Available RAM: {get_available_ram_gb():.2f} GB")
    logger.info(f"Config max RAM: {config.get('max_ram_gb', 7)} GB")
    
    # Note: Actual file processing requires a real input file.
    # This main function does not execute file I/O to avoid side effects.

if __name__ == "__main__":
    main()
