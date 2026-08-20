"""
Memory-efficient streaming utilities for large NIfTI files.

This module provides generators and functions to process NIfTI images
in chunks (time or space) to ensure RAM usage stays below 7GB.
"""
import os
import numpy as np
import nibabel as nib
from pathlib import Path
from typing import Generator, Tuple, Optional, List, Union
from config import ensure_directories

# Constants
MAX_RAM_GB = 7.0
BYTES_PER_FLOAT32 = 4
GB_TO_BYTES = 1024 ** 3


def get_nifti_volume_info(nifti_path: Union[str, Path]) -> dict:
    """
    Inspect a NIfTI file without loading the full data array.
    
    Returns metadata including dimensions, data type, and estimated memory size.
    
    Args:
        nifti_path: Path to the .nii or .nii.gz file.
        
    Returns:
        Dictionary containing shape, dtype, estimated_size_gb, and voxel_size.
    """
    path = Path(nifti_path)
    if not path.exists():
        raise FileNotFoundError(f"NIfTI file not found: {nifti_path}")
    
    # Load header only
    img = nib.load(str(path))
    header = img.header
    data_shape = img.shape
    data_dtype = img.get_data_dtype()
    
    # Calculate total size
    total_voxels = np.prod(data_shape)
    bytes_per_voxel = data_dtype.itemsize
    total_bytes = total_voxels * bytes_per_voxel
    total_size_gb = total_bytes / GB_TO_BYTES
    
    return {
        "shape": data_shape,
        "dtype": str(data_dtype),
        "estimated_size_gb": round(total_size_gb, 2),
        "voxel_size": img.header.get_zooms(),
        "ndim": len(data_shape)
    }


def verify_memory_constraints(nifti_path: Union[str, Path], max_gb: float = MAX_RAM_GB) -> bool:
    """
    Check if loading the entire NIfTI file would exceed memory constraints.
    
    Args:
        nifti_path: Path to the NIfTI file.
        max_gb: Maximum allowed RAM in GB (default 7.0).
        
    Returns:
        True if the file fits in memory, False otherwise.
        
    Raises:
        RuntimeError: If the file exceeds memory constraints.
    """
    info = get_nifti_volume_info(nifti_path)
    if info["estimated_size_gb"] > max_gb:
        raise RuntimeError(
            f"Memory constraint violation: {nifti_path} is {info['estimated_size_gb']}GB, "
            f"exceeding limit of {max_gb}GB. Use streaming utilities instead."
        )
    return True


def stream_nifti_by_time_chunks(
    nifti_path: Union[str, Path],
    chunk_size: int = 10,
    overlap: int = 0
) -> Generator[Tuple[int, np.ndarray], None, None]:
    """
    Stream a 4D NIfTI file (x, y, z, time) in time-based chunks.
    
    This allows processing long time-series without loading the full 4D array.
    
    Args:
        nifti_path: Path to the 4D NIfTI file.
        chunk_size: Number of timepoints per chunk.
        overlap: Number of timepoints to overlap between chunks.
        
    Yields:
        Tuples of (start_index, data_chunk) where data_chunk shape is (x, y, z, chunk_size).
    """
    path = Path(nifti_path)
    if not path.exists():
        raise FileNotFoundError(f"NIfTI file not found: {nifti_path}")
    
    img = nib.load(str(path))
    data_shape = img.shape
    
    if len(data_shape) != 4:
        raise ValueError(f"Expected 4D NIfTI, got shape {data_shape}")
    
    x, y, z, t = data_shape
    start_idx = 0
    
    while start_idx < t:
        end_idx = min(start_idx + chunk_size, t)
        
        # Use memory mapping for efficient slicing
        # nibabel's get_fdata() loads the whole file, so we use dataobj directly
        # which supports slicing without full load for many formats
        data_obj = img.dataobj
        
        # Slicing the dataobj creates a view or reads only necessary blocks
        # depending on the underlying file format and compression
        chunk = data_obj[:, :, :, start_idx:end_idx]
        
        # Convert to numpy array (only the chunk is loaded into RAM)
        chunk_array = np.asarray(chunk)
        
        yield (start_idx, chunk_array)
        
        start_idx = end_idx - overlap if overlap > 0 else end_idx


def stream_nifti_by_spatial_chunks(
    nifti_path: Union[str, Path],
    chunk_size: Tuple[int, int, int] = (32, 32, 32)
) -> Generator[Tuple[Tuple[int, int, int], np.ndarray], None, None]:
    """
    Stream a 3D or 4D NIfTI file in spatial chunks.
    
    Useful for operations that can be parallelized over brain regions.
    
    Args:
        nifti_path: Path to the NIfTI file.
        chunk_size: Tuple (dx, dy, dz) defining the spatial block size.
        
    Yields:
        Tuples of ((x_start, y_start, z_start), data_chunk).
    """
    path = Path(nifti_path)
    if not path.exists():
        raise FileNotFoundError(f"NIfTI file not found: {nifti_path}")
    
    img = nib.load(str(path))
    data_shape = img.shape
    data_obj = img.dataobj
    
    dx, dy, dz = chunk_size
    x_dim, y_dim, z_dim = data_shape[:3]
    t_dim = data_shape[3] if len(data_shape) == 4 else 1
    
    for x_start in range(0, x_dim, dx):
        x_end = min(x_start + dx, x_dim)
        for y_start in range(0, y_dim, dy):
            y_end = min(y_start + dy, y_dim)
            for z_start in range(0, z_dim, dz):
                z_end = min(z_start + dz, z_dim)
                
                if len(data_shape) == 4:
                    chunk = data_obj[x_start:x_end, y_start:y_end, z_start:z_end, :]
                else:
                    chunk = data_obj[x_start:x_end, y_start:y_end, z_start:z_end]
                
                yield ((x_start, y_start, z_start), np.asarray(chunk))


def extract_roi_timeseries_streaming(
    nifti_path: Union[str, Path],
    mask_path: Union[str, Path],
    chunk_size: int = 50
) -> np.ndarray:
    """
    Extract ROI timeseries from a NIfTI file using a mask, processing in time chunks.
    
    This avoids loading the full 4D image and full mask into memory simultaneously.
    
    Args:
        nifti_path: Path to the 4D NIfTI file (BOLD data).
        mask_path: Path to the binary mask (3D NIfTI).
        chunk_size: Number of timepoints to process per chunk.
        
    Returns:
        2D numpy array (n_voxels_in_roi, n_timepoints).
    """
    path = Path(nifti_path)
    mask_path = Path(mask_path)
    
    if not path.exists():
        raise FileNotFoundError(f"NIfTI file not found: {nifti_path}")
    if not mask_path.exists():
        raise FileNotFoundError(f"Mask file not found: {mask_path}")
    
    # Load mask (usually small)
    mask_img = nib.load(str(mask_path))
    mask_data = np.asarray(mask_img.dataobj)
    roi_indices = np.where(mask_data > 0)
    n_voxels = len(roi_indices[0])
    
    if n_voxels == 0:
        raise ValueError("Mask contains no valid voxels.")
    
    # Load image info
    img = nib.load(str(path))
    data_obj = img.dataobj
    _, _, _, n_timepoints = data_obj.shape
    
    # Prepare output array
    timeseries = np.zeros((n_voxels, n_timepoints), dtype=np.float32)
    
    # Stream time chunks
    start_idx = 0
    voxel_idx = 0
    while start_idx < n_timepoints:
        end_idx = min(start_idx + chunk_size, n_timepoints)
        chunk = np.asarray(data_obj[:, :, :, start_idx:end_idx])
        
        # Extract ROI voxels for this chunk
        # chunk shape: (x, y, z, t_chunk)
        # We need to extract specific (x, y, z) coordinates for all t
        for i in range(n_voxels):
            x, y, z = roi_indices[0][i], roi_indices[1][i], roi_indices[2][i]
            timeseries[i, start_idx:end_idx] = chunk[x, y, z, :]
        
        start_idx = end_idx
    
    return timeseries


def main():
    """
    Command-line interface for testing streaming utilities.
    Usage: python code/streaming_utils.py <nifti_path> [--chunk-size 10]
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python code/streaming_utils.py <nifti_path> [--chunk-size N]")
        sys.exit(1)
    
    nifti_path = sys.argv[1]
    chunk_size = 10
    
    for i, arg in enumerate(sys.argv):
        if arg == "--chunk-size" and i + 1 < len(sys.argv):
            chunk_size = int(sys.argv[i + 1])
    
    print(f"Analyzing: {nifti_path}")
    
    try:
        info = get_nifti_volume_info(nifti_path)
        print(f"Shape: {info['shape']}")
        print(f"Dtype: {info['dtype']}")
        print(f"Estimated Size: {info['estimated_size_gb']} GB")
        
        if info['estimated_size_gb'] > MAX_RAM_GB:
            print(f"Warning: File exceeds {MAX_RAM_GB}GB limit. Using streaming.")
            print(f"Streaming chunks of {chunk_size} timepoints...")
            count = 0
            for start_idx, chunk in stream_nifti_by_time_chunks(nifti_path, chunk_size):
                count += 1
                print(f"  Processed chunk {count}: timepoints {start_idx}-{start_idx+chunk.shape[-1]}")
                # Free memory explicitly
                del chunk
            print(f"Completed processing {count} chunks.")
        else:
            print("File fits in memory. Full load test skipped for safety.")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()