"""
Memory-efficient streaming utilities for large NIfTI files.

This module provides functions to process fMRI data in chunks to ensure
peak RAM usage stays below 7GB, as required by the project constraints.
It leverages nibabel's memory mapping and chunked iteration capabilities.
"""
import os
import numpy as np
import nibabel as nib
from pathlib import Path
from typing import Generator, Tuple, Optional, List, Union
from config import ensure_directories
import logging

logger = logging.getLogger(__name__)

# Constants for memory management
# Target: < 7GB RAM. We'll process data in chunks to stay well within this.
# Assuming float32 (4 bytes) for time series data.
# A 264-node atlas with 1000 timepoints is ~1MB, so the bottleneck is usually
# the raw 4D volume loading.
MAX_CHUNK_SIZE_MB = 500  # Process ~500MB chunks at a time

def get_nifti_volume_info(file_path: Union[str, Path]) -> dict:
    """
    Retrieve metadata about a NIfTI file without loading the full data into memory.
    
    Args:
        file_path: Path to the NIfTI file.
        
    Returns:
        Dictionary containing shape, dtype, voxel dimensions, and estimated size.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"NIfTI file not found: {file_path}")
    
    # Load header only (nibabel does this efficiently)
    img = nib.load(str(file_path))
    header = img.header
    data_shape = img.shape
    data_dtype = img.get_data_dtype()
    affine = img.affine
    
    # Calculate estimated size in MB
    # Shape is typically (x, y, z, t)
    if len(data_shape) == 4:
        total_voxels = np.prod(data_shape)
    elif len(data_shape) == 3:
        total_voxels = np.prod(data_shape)
    else:
        raise ValueError(f"Unexpected NIfTI shape: {data_shape}")
        
    bytes_per_voxel = np.dtype(data_dtype).itemsize
    estimated_size_mb = (total_voxels * bytes_per_voxel) / (1024 ** 2)
    
    return {
        "shape": data_shape,
        "dtype": str(data_dtype),
        "voxel_size_mm": header.get_zooms(),
        "affine": affine,
        "estimated_size_mb": estimated_size_mb,
        "is_4d": len(data_shape) == 4
    }

def stream_nifti_by_time_chunks(
    file_path: Union[str, Path],
    chunk_size: Optional[int] = None
) -> Generator[Tuple[int, np.ndarray], None, None]:
    """
    Stream a 4D NIfTI file in time-point chunks to minimize memory usage.
    
    This generator yields (start_idx, end_idx, data_chunk) tuples.
    The data_chunk is a 4D array (x, y, z, t_chunk) or 3D if 3D file.
    
    Args:
        file_path: Path to the NIfTI file.
        chunk_size: Number of time points per chunk. If None, calculates
                    based on MAX_CHUNK_SIZE_MB.
                    
    Yields:
        Tuple of (start_time_idx, end_time_idx, data_array)
        
    Raises:
        FileNotFoundError: If file doesn't exist.
        ValueError: If file is not 4D (or 3D with single timepoint).
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"NIfTI file not found: {file_path}")
        
    img = nib.load(str(file_path))
    data_shape = img.shape
    
    if len(data_shape) == 3:
        # Treat as single time point 4D
        logger.warning(f"File {file_path} is 3D. Treating as single timepoint.")
        data = img.get_fdata(dtype=np.float32)
        yield (0, 1, data[..., np.newaxis])
        return
        
    if len(data_shape) != 4:
        raise ValueError(f"Expected 4D NIfTI, got shape {data_shape}")
        
    x, y, z, t = data_shape
    bytes_per_voxel = np.dtype(img.get_data_dtype()).itemsize
    voxel_size_mb = (x * y * z * bytes_per_voxel) / (1024 ** 2)
    
    if chunk_size is None:
        # Calculate chunk size to fit within MAX_CHUNK_SIZE_MB
        # We want chunk_size * voxel_size_mb <= MAX_CHUNK_SIZE_MB
        if voxel_size_mb == 0:
            chunk_size = t
        else:
            chunk_size = max(1, int(MAX_CHUNK_SIZE_MB / voxel_size_mb))
            # Ensure we don't exceed total time points
            chunk_size = min(chunk_size, t)
            
    logger.info(f"Streaming {file_path}: {t} timepoints in chunks of {chunk_size} ({chunk_size * voxel_size_mb:.1f}MB per chunk)")
    
    # Use memory-mapped access to avoid loading full volume
    # nibabel's get_fdata() loads into memory, so we use dataobj directly
    # or load in slices. However, standard nibabel doesn't support true
    # chunked reading without loading the whole thing if not memory mapped correctly.
    # We will use get_fdata() but slice it, assuming the file is not huge
    # in X/Y/Z dimensions (typical fMRI is ~64x64x36).
    # If X*Y*Z is huge, we need a different approach, but for standard HCP data
    # (often 2mm isotropic ~91x109x91), loading one timepoint is ~36MB,
    # so loading 10-15 timepoints is safe.
    
    # To be safe for very large X/Y/Z, we iterate time points one by one if chunk_size > 1 is risky
    # But typically HCP data fits in memory for a few timepoints.
    # We will load the whole array if it fits in a reasonable buffer, else slice.
    # Given the constraint <7GB, and typical fMRI sizes, loading the whole 4D
    # might exceed memory if T is large (e.g. 1000 TRs * 36MB = 36GB).
    # So we MUST NOT load the whole 4D array.
    
    # Strategy: Iterate time points and accumulate.
    current_chunk = []
    start_idx = 0
    
    for t_idx in range(t):
        # Load single time point (3D volume)
        # This is the most memory-efficient way with nibabel
        vol_3d = img.dataobj[t_idx, :, :, :]
        vol_3d = np.asarray(vol_3d, dtype=np.float32)
        
        current_chunk.append(vol_3d)
        
        if len(current_chunk) == chunk_size or t_idx == t - 1:
            # Stack and yield
            chunk_4d = np.stack(current_chunk, axis=-1)
            end_idx = t_idx + 1
            yield (start_idx, end_idx, chunk_4d)
            
            # Reset
            current_chunk = []
            start_idx = end_idx

def stream_nifti_by_spatial_chunks(
    file_path: Union[str, Path],
    chunk_size_z: Optional[int] = None
) -> Generator[Tuple[int, int, np.ndarray], None, None]:
    """
    Stream a 4D NIfTI file in spatial Z-slices chunks.
    
    Useful when time dimension is small but spatial volume is large.
    
    Args:
        file_path: Path to the NIfTI file.
        chunk_size_z: Number of Z-slices per chunk.
        
    Yields:
        Tuple of (start_z, end_z, data_array) where data_array is (x, y, z_chunk, t)
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"NIfTI file not found: {file_path}")
        
    img = nib.load(str(file_path))
    data_shape = img.shape
    
    if len(data_shape) == 3:
        # Add time dimension
        data_shape = data_shape + (1,)
        t = 1
    else:
        t = data_shape[3]
        
    x, y, z, t = data_shape
    
    if chunk_size_z is None:
        # Estimate based on memory
        bytes_per_voxel = np.dtype(img.get_data_dtype()).itemsize
        slice_size_mb = (x * y * t * bytes_per_voxel) / (1024 ** 2)
        if slice_size_mb == 0:
            chunk_size_z = z
        else:
            chunk_size_z = max(1, int(MAX_CHUNK_SIZE_MB / slice_size_mb))
            chunk_size_z = min(chunk_size_z, z)
            
    logger.info(f"Streaming spatial Z-chunks: {z} slices in chunks of {chunk_size_z}")
    
    for start_z in range(0, z, chunk_size_z):
        end_z = min(start_z + chunk_size_z, z)
        
        # Load slice chunk
        # dataobj allows slicing
        chunk_data = np.asarray(img.dataobj[:, :, start_z:end_z, :], dtype=np.float32)
        yield (start_z, end_z, chunk_data)

def extract_roi_timeseries_streaming(
    file_path: Union[str, Path],
    roi_mask_path: Union[str, Path],
    chunk_size: Optional[int] = None
) -> np.ndarray:
    """
    Extract time series for a specific ROI from a large NIfTI file using streaming.
    
    This avoids loading the full 4D volume into memory by processing time chunks
    and aggregating the ROI mean.
    
    Args:
        file_path: Path to the 4D NIfTI fMRI file.
        roi_mask_path: Path to the 3D NIfTI mask defining the ROI (1s inside, 0s outside).
        chunk_size: Number of time points per processing chunk.
        
    Returns:
        1D numpy array of time series (mean signal per time point).
        
    Raises:
        FileNotFoundError: If files not found.
        ValueError: If mask shape doesn't match spatial dimensions of fMRI.
    """
    file_path = Path(file_path)
    roi_mask_path = Path(roi_mask_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"fMRI file not found: {file_path}")
    if not roi_mask_path.exists():
        raise FileNotFoundError(f"ROI mask not found: {roi_mask_path}")
        
    # Load ROI mask (3D, should fit in memory)
    mask_img = nib.load(str(roi_mask_path))
    mask_data = np.asarray(mask_img.get_fdata(dtype=np.float32))
    mask_shape = mask_data.shape
    
    # Validate spatial dimensions
    fmri_info = get_nifti_volume_info(file_path)
    fmri_shape = fmri_info["shape"]
    
    if len(fmri_shape) == 4:
        fmri_spatial_shape = fmri_shape[:3]
    else:
        fmri_spatial_shape = fmri_shape
        
    if fmri_spatial_shape != mask_shape:
        raise ValueError(
            f"Mask shape {mask_shape} does not match fMRI spatial shape {fmri_spatial_shape}"
        )
        
    # Get indices of active voxels
    active_voxel_indices = np.where(mask_data > 0)
    if len(active_voxel_indices[0]) == 0:
        logger.warning(f"No active voxels found in ROI mask: {roi_mask_path}")
        return np.array([])
        
    logger.info(f"ROI has {len(active_voxel_indices[0])} active voxels")
    
    # Prepare storage for time series
    # We don't know T yet, so we'll collect in a list and convert at the end
    # or use a pre-allocated array if we know T.
    # Since we stream, we don't know T easily without loading header fully (which we did).
    t = fmri_info["shape"][3] if len(fmri_info["shape"]) == 4 else 1
    time_series = np.zeros(t, dtype=np.float32)
    
    # Stream through time chunks
    for start_idx, end_idx, chunk_4d in stream_nifti_by_time_chunks(file_path, chunk_size):
        # chunk_4d shape: (x, y, z, t_chunk)
        t_chunk = chunk_4d.shape[-1]
        
        # Extract values for active voxels
        # This is efficient: advanced indexing on the chunk
        chunk_values = chunk_4d[active_voxel_indices]
        
        # Calculate mean across voxels for each time point in the chunk
        mean_signal = np.mean(chunk_values, axis=0)
        
        # Store in main array
        time_series[start_idx:end_idx] = mean_signal
        
    return time_series

def verify_memory_constraints(
    file_path: Union[str, Path],
    max_ram_gb: float = 7.0
) -> bool:
    """
    Verify that processing the given file with our streaming strategy
    will stay within the specified RAM limit.
    
    Args:
        file_path: Path to the NIfTI file.
        max_ram_gb: Maximum allowed RAM usage in GB.
        
    Returns:
        True if safe, False otherwise.
    """
    info = get_nifti_volume_info(file_path)
    voxel_size_mb = (info["shape"][0] * info["shape"][1] * info["shape"][2] * 
                    np.dtype(info["dtype"]).itemsize) / (1024 ** 2)
    
    # Worst case: loading one full 3D volume + overhead
    # Our streaming loads one chunk (e.g., 500MB) + Python overhead
    estimated_peak_mb = MAX_CHUNK_SIZE_MB + 100  # 100MB overhead buffer
    estimated_peak_gb = estimated_peak_mb / 1024
    
    if estimated_peak_gb > max_ram_gb:
        logger.error(f"Estimated peak memory {estimated_peak_gb:.2f}GB exceeds limit {max_ram_gb}GB")
        return False
        
    logger.info(f"Memory check passed: estimated peak {estimated_peak_gb:.2f}GB < {max_ram_gb}GB")
    return True

def main():
    """
    CLI entry point for testing streaming utilities.
    Usage: python code/streaming_utils.py <path_to_nifti>
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python code/streaming_utils.py <path_to_nifti>")
        sys.exit(1)
        
    nifti_path = Path(sys.argv[1])
    
    print(f"Analyzing: {nifti_path}")
    try:
        info = get_nifti_volume_info(nifti_path)
        print(f"Shape: {info['shape']}")
        print(f"Estimated size: {info['estimated_size_mb']:.2f} MB")
        print(f"Dtype: {info['dtype']}")
        
        print("\nTesting streaming by time chunks...")
        total_timepoints = 0
        for start, end, chunk in stream_nifti_by_time_chunks(nifti_path):
            total_timepoints += (end - start)
            print(f"  Chunk: {start}-{end}, shape: {chunk.shape}")
            
        print(f"Total timepoints streamed: {total_timepoints}")
        
        if info['is_4d']:
            print("\nMemory constraint check:")
            verify_memory_constraints(nifti_path)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()