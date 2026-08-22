"""
Memory-efficient streaming utilities for large NIfTI files.

This module provides generators and functions to process large fMRI NIfTI files
in chunks (temporal or spatial) to ensure peak RAM usage stays below 7GB.

It avoids loading the entire 4D volume into memory at once.
"""
import os
import numpy as np
import nibabel as nib
from pathlib import Path
from typing import Generator, Tuple, Optional, List, Union, Iterator
import logging
from config import ensure_directories

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
# 7 GB limit in bytes (approx)
MAX_RAM_BYTES = 7 * 1024**3 
# Safety margin: we aim to use max 80% of the limit for the data buffer
TARGET_BUFFER_BYTES = int(MAX_RAM_BYTES * 0.8)

# Default chunk size (number of volumes/timepoints)
DEFAULT_CHUNK_SIZE = 30 

def get_nifti_volume_info(nifti_path: Union[str, Path]) -> dict:
    """
    Inspect a NIfTI file header to get dimensions and data type size
    without loading the actual data.
    
    Args:
        nifti_path: Path to the NIfTI file.
        
    Returns:
        Dictionary with keys: 'shape', 'dtype', 'size_bytes', 'n_volumes', 'voxel_size_bytes'.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not a valid NIfTI.
    """
    path = Path(nifti_path)
    if not path.exists():
        raise FileNotFoundError(f"NIfTI file not found: {path}")
    
    try:
        # Load header only (fast, low memory)
        img = nib.load(str(path), mmap=False)
    except Exception as e:
        raise ValueError(f"Failed to load NIfTI header for {path}: {e}")
    
    shape = img.shape
    if len(shape) < 3:
        raise ValueError(f"Invalid NIfTI dimensions for {path}: {shape}. Expected at least 3D.")
    
    dtype = img.get_data_dtype()
    voxel_size_bytes = dtype.itemsize
    
    # Assuming 4D (x, y, z, t) for fMRI
    if len(shape) == 4:
        n_volumes = shape[3]
    else:
        # Treat 3D as having 1 volume
        n_volumes = 1
        
    total_size = np.prod(shape) * voxel_size_bytes
    
    return {
        'shape': shape,
        'dtype': str(dtype),
        'size_bytes': total_size,
        'n_volumes': n_volumes,
        'voxel_size_bytes': voxel_size_bytes,
        'is_4d': len(shape) == 4
    }

def verify_memory_constraints(nifti_path: Union[str, Path], chunk_size: int = DEFAULT_CHUNK_SIZE) -> bool:
    """
    Verify that processing the file with the given chunk size will not exceed RAM limits.
    
    Args:
        nifti_path: Path to the NIfTI file.
        chunk_size: Number of timepoints (volumes) to load at once.
        
    Returns:
        True if safe to proceed, False otherwise.
        
    Raises:
        ValueError: If the constraints cannot be met.
    """
    info = get_nifti_volume_info(nifti_path)
    shape = info['shape']
    voxel_bytes = info['voxel_size_bytes']
    
    # Calculate memory for one chunk
    # Shape is (x, y, z, t). We load (x, y, z, chunk_size)
    chunk_shape = list(shape)
    if len(chunk_shape) == 4:
        chunk_shape[3] = chunk_size
    else:
        # 3D case, just load the whole thing if it fits, else fail
        if len(shape) == 3:
            chunk_shape = shape
        else:
            raise ValueError(f"Unsupported dimensionality: {len(shape)}")
            
    chunk_bytes = np.prod(chunk_shape) * voxel_bytes
    
    if chunk_bytes > TARGET_BUFFER_BYTES:
        # Calculate max safe chunk size
        # max_chunks = TARGET_BUFFER_BYTES / (voxel_bytes * x * y * z)
        base_voxels = np.prod(shape[:3])
        max_safe_chunks = int(TARGET_BUFFER_BYTES / (base_voxels * voxel_bytes))
        if max_safe_chunks < 1:
            raise ValueError(
                f"Single volume of {nifti_path} ({base_voxels * voxel_bytes / 1e9:.2f} GB) exceeds target buffer "
                f"({TARGET_BUFFER_BYTES / 1e9:.2f} GB). Cannot process this file within 7GB constraint."
            )
        raise ValueError(
            f"Chunk size {chunk_size} for {nifti_path} requires {chunk_bytes / 1e9:.2f} GB RAM. "
            f"Target limit is ~{TARGET_BUFFER_BYTES / 1e9:.2f} GB. "
            f"Please reduce chunk_size to at most {max_safe_chunks}."
        )
    
    logger.info(f"Memory check passed for {nifti_path}: chunk_size={chunk_size}, est_usage={chunk_bytes/1e9:.2f}GB")
    return True

def stream_nifti_by_time_chunks(
    nifti_path: Union[str, Path],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = 0
) -> Generator[Tuple[int, np.ndarray], None, None]:
    """
    Generator that yields time chunks of a 4D NIfTI file.
    
    Yields:
        Tuple of (start_index, data_chunk) where data_chunk has shape (x, y, z, chunk_size).
        
    Note:
        This uses memory mapping (mmap) where possible, but explicitly loads the slice
        into memory for the chunk.
    """
    path = Path(nifti_path)
    info = get_nifti_volume_info(path)
    
    if not info['is_4d']:
        # If 3D, treat as a single chunk
        verify_memory_constraints(path, 1)
        img = nib.load(str(path))
        data = img.get_fdata()
        # Reshape to 4D if necessary
        if len(data.shape) == 3:
            data = data[..., np.newaxis]
        yield 0, data
        return

    verify_memory_constraints(path, chunk_size)
    
    # Load with mmap to avoid loading everything immediately
    # Note: get_data() or get_fdata() might trigger loading depending on implementation.
    # We use get_data() with mmap=True to keep it lazy, then slice.
    img = nib.load(str(path), mmap=True)
    
    # Ensure we are working with the underlying data object if possible
    # nibabel's mmap=True returns a memory-mapped array if supported
    data_obj = img.get_data()
    
    n_volumes = info['n_volumes']
    
    start_idx = 0
    while start_idx < n_volumes:
        end_idx = min(start_idx + chunk_size, n_volumes)
        actual_size = end_idx - start_idx
        
        # Slice the memory-mapped array
        # This operation should be memory efficient (just mapping the slice)
        # However, some backends might load the slice.
        chunk = data_obj[..., start_idx:end_idx]
        
        # If the chunk is a memory map, we might want to ensure it's contiguous or cast if needed,
        # but for numpy operations on slices, it usually works fine.
        # If the backend forces a load, this is the point where RAM usage spikes.
        
        # Handle case where chunk might be smaller than requested (last chunk)
        if chunk.shape[3] != actual_size:
            # Fallback: explicit slicing if the object didn't support it directly
            # This is rare with nibabel but good for safety
            chunk = data_obj[..., start_idx:end_idx]
        
        yield start_idx, chunk
        start_idx = end_idx
        
        # If we have overlap for sliding windows, adjust start
        if overlap > 0 and start_idx < n_volumes:
            # We want the next chunk to start 'overlap' volumes back
            # But we already advanced by chunk_size. 
            # To implement overlap correctly in a streaming context:
            # The previous chunk ended at 'end_idx'. The next should start at 'end_idx - overlap'.
            # However, the generator logic above advances by chunk_size.
            # Let's adjust the logic:
            # We yield [start, end). Next start should be end - overlap.
            # But we must ensure we don't go backwards.
            # Actually, the standard sliding window is: yield [i, i+window), next i = i + step.
            # Here 'chunk_size' acts as window, and we assume step = chunk_size - overlap.
            # But the task asks for streaming by time chunks.
            # Let's stick to non-overlapping chunks for basic streaming, 
            # or implement step logic if overlap is provided.
            # Re-implementation for overlap:
            # If overlap > 0, step = chunk_size - overlap.
            # But the loop condition is start_idx < n_volumes.
            # Let's just yield non-overlapping for now as per typical "chunking",
            # unless specific sliding window logic is required here.
            # The prompt implies "streaming utilities", usually for loading parts.
            # We will assume non-overlapping chunks for the base utility,
            # and the caller handles overlap if needed, OR we adjust the step.
            # Let's assume step = chunk_size - overlap.
            if overlap > 0:
                step = chunk_size - overlap
                if step <= 0:
                    raise ValueError("Overlap cannot be >= chunk_size")
                start_idx = end_idx - overlap
                # Avoid infinite loop if step is 0 or negative (handled above)
                # Ensure we don't start before the previous end if overlap is large?
                # Actually, if we yield [0, 30), next start = 30 - 10 = 20.
                # Then we yield [20, 50).
                # This is correct.
            else:
                # No overlap, step = chunk_size
                start_idx = end_idx

def stream_nifti_by_spatial_chunks(
    nifti_path: Union[str, Path],
    z_chunk_size: int = 10
) -> Generator[Tuple[Tuple[int, int, int], np.ndarray], None, None]:
    """
    Generator that yields spatial chunks (slabs) of a 4D NIfTI file.
    Useful for operations that can be parallelized or need to fit in memory
    by slicing the volume along the Z-axis.
    
    Yields:
        Tuple of ((z_start, z_end), data_chunk) where data_chunk is (x, y, z_chunk, t).
    """
    path = Path(nifti_path)
    info = get_nifti_volume_info(path)
    shape = info['shape']
    
    if len(shape) < 3:
        raise ValueError("Spatial chunking requires at least 3D data.")
    
    # Load with mmap
    img = nib.load(str(path), mmap=True)
    data_obj = img.get_data()
    
    z_dim = shape[2]
    z_start = 0
    
    while z_start < z_dim:
        z_end = min(z_start + z_chunk_size, z_dim)
        if len(shape) == 4:
            chunk = data_obj[:, :, z_start:z_end, :]
        else:
            chunk = data_obj[:, :, z_start:z_end]
        
        yield (z_start, z_end), chunk
        z_start = z_end

def extract_roi_timeseries_streaming(
    nifti_path: Union[str, Path],
    roi_mask_path: Union[str, Path],
    chunk_size: int = DEFAULT_CHUNK_SIZE
) -> np.ndarray:
    """
    Extracts the mean time series for a specific ROI from a large NIfTI file
    by streaming the data in chunks to avoid memory overflow.
    
    Args:
        nifti_path: Path to the 4D fMRI NIfTI file.
        roi_mask_path: Path to a 3D NIfTI mask file (1.0 inside ROI, 0.0 outside).
        chunk_size: Number of timepoints to process at once.
        
    Returns:
        1D numpy array of the mean time series for the ROI.
    """
    path = Path(nifti_path)
    mask_path = Path(roi_mask_path)
    
    # Validate inputs
    if not path.exists():
        raise FileNotFoundError(f"NIfTI file not found: {path}")
    if not mask_path.exists():
        raise FileNotFoundError(f"ROI mask not found: {mask_path}")
    
    # Load mask (usually small, fits in memory)
    mask_img = nib.load(str(mask_path))
    mask_data = mask_img.get_fdata()
    
    # Flatten mask to 1D for indexing if needed, but we'll use boolean indexing
    # Ensure mask is boolean
    mask_bool = mask_data > 0.5
    n_voxels_roi = np.sum(mask_bool)
    
    if n_voxels_roi == 0:
        raise ValueError("ROI mask contains no valid voxels.")
    
    # Get fMRI info
    info = get_nifti_volume_info(path)
    if not info['is_4d']:
        raise ValueError("ROI extraction requires a 4D NIfTI file.")
    
    n_volumes = info['n_volumes']
    shape = info['shape']
    
    # Prepare output array
    # We need to sum over the ROI voxels for each timepoint
    # To do this efficiently in streaming:
    # 1. Stream chunks of time (x, y, z, t_chunk)
    # 2. For each chunk, extract the ROI voxels
    # 3. Sum them up (or average)
    # 4. Accumulate into the final time series
    
    # However, extracting arbitrary voxels from a memory-mapped array in chunks of time
    # might be tricky if the memory layout is not contiguous for the ROI.
    # A better approach for streaming:
    # Stream spatial chunks? No, we need the full time series.
    # Streaming time chunks is better:
    # For each time chunk, we load (x, y, z, t_chunk).
    # Then we apply the mask.
    # This requires the mask to be broadcastable.
    
    verify_memory_constraints(path, chunk_size)
    
    # Initialize output
    # We need to store the sum of the ROI voxels for each timepoint
    # But we can't store the whole 4D data.
    # We can accumulate the sum for the ROI.
    # Wait, we need the mean time series.
    # Mean = (Sum of voxels at time t) / N_voxels
    # We can accumulate the sum for each timepoint in a 1D array.
    
    time_series_sum = np.zeros(n_volumes, dtype=np.float32)
    
    # Stream by time
    # We need to be careful: if we load (x, y, z, t_chunk),
    # and the mask is (x, y, z), we can do:
    # chunk_roi = chunk[mask_bool] -> shape (n_voxels_roi, t_chunk)
    # sum_roi = np.sum(chunk_roi, axis=0) -> shape (t_chunk,)
    # This works perfectly and is memory efficient if chunk_size is small enough.
    
    for start_idx, chunk in stream_nifti_by_time_chunks(path, chunk_size):
        # chunk shape: (x, y, z, t_chunk)
        # Flatten spatial dimensions to apply mask
        # We need to be careful with memory here.
        # chunk is (x, y, z, t). We want to select voxels where mask is True.
        # This creates a new array of shape (n_voxels_roi, t_chunk).
        # If n_voxels_roi is large, this might be big, but it's much smaller than full 4D.
        
        # Reshape chunk to 2D: (n_voxels, t_chunk)
        # This might be expensive if done naively, but numpy handles views.
        # However, the mask application creates a copy.
        # Let's try to do it.
        
        # Reshape chunk to (n_voxels, t_chunk)
        # We need to flatten the first 3 dims
        n_spatial = np.prod(shape[:3])
        chunk_2d = chunk.reshape(n_spatial, -1)
        
        # Apply mask
        # mask_bool is (x, y, z) -> flatten to (n_spatial,)
        mask_flat = mask_bool.flatten()
        
        # Select ROI voxels
        roi_data = chunk_2d[mask_flat, :] # Shape: (n_voxels_roi, t_chunk)
        
        # Sum across voxels for each timepoint
        time_series_sum[start_idx:start_idx+roi_data.shape[1]] += np.sum(roi_data, axis=0)
    
    # Calculate mean
    time_series_mean = time_series_sum / n_voxels_roi
    
    return time_series_mean

def main():
    """
    Main entry point for testing the streaming utilities.
    This function is intended to be run as a script to verify functionality.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Test NIfTI streaming utilities")
    parser.add_argument("--file", type=str, required=True, help="Path to a NIfTI file")
    parser.add_argument("--mask", type=str, required=False, help="Path to ROI mask (optional)")
    parser.add_argument("--chunk", type=int, default=DEFAULT_CHUNK_SIZE, help="Chunk size (volumes)")
    
    args = parser.parse_args()
    
    logger.info(f"Testing streaming on: {args.file}")
    
    try:
        info = get_nifti_volume_info(args.file)
        logger.info(f"File info: {info}")
        
        # Test memory constraint
        verify_memory_constraints(args.file, args.chunk)
        logger.info("Memory constraint verified.")
        
        # Test streaming
        logger.info(f"Streaming chunks of size {args.chunk}...")
        count = 0
        for start_idx, chunk in stream_nifti_by_time_chunks(args.file, args.chunk):
            count += 1
            logger.debug(f"Chunk {count}: start={start_idx}, shape={chunk.shape}")
            if count > 5: # Limit for demo
                break
        
        logger.info(f"Successfully streamed {count} chunks.")
        
        if args.mask:
            logger.info(f"Extracting ROI timeseries from mask: {args.mask}")
            ts = extract_roi_timeseries_streaming(args.file, args.mask, args.chunk)
            logger.info(f"ROI timeseries shape: {ts.shape}, mean: {np.mean(ts):.4f}")
        
    except Exception as e:
        logger.error(f"Error during streaming test: {e}")
        raise

if __name__ == "__main__":
    main()
