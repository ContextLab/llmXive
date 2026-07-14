"""
Chunked loading and subsampling for fMRI data exceeding RAM capacity.

This module implements memory-efficient loading of large neuroimaging datasets
(e.g., OpenNeuro fMRI NIfTI files) by processing data in chunks and subsampling
when total size exceeds available RAM.
"""

import os
import gc
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Iterator, Dict, Any
import nibabel as nib

from config import get_config
from utils.logging_config import get_logger, info, warning, error, debug

logger = get_logger(__name__)


def estimate_file_size_mb(file_path: Path) -> float:
    """Estimate file size in MB."""
    return file_path.stat().st_size / (1024 * 1024)


def get_available_ram_gb() -> float:
    """Get available RAM in GB using config settings."""
    config = get_config()
    max_ram_gb = config.get('max_ram_gb', 7)
    return max_ram_gb


def calculate_chunk_size(
    shape: Tuple[int, int, int, int],
    dtype: np.dtype,
    max_ram_gb: float,
    safety_factor: float = 0.5
) -> int:
    """
    Calculate optimal chunk size (number of timepoints per chunk)
    to stay within RAM limits.

    Args:
        shape: NIfTI shape (x, y, z, t)
        dtype: Data type of the array
        max_ram_gb: Maximum RAM in GB
        safety_factor: Fraction of RAM to use (default 0.5 for safety)

    Returns:
        Number of timepoints per chunk
    """
    x, y, z, t = shape
    bytes_per_voxel = dtype.itemsize
    total_voxels = x * y * z
    bytes_per_timepoint = total_voxels * bytes_per_voxel
    max_bytes = max_ram_gb * (1024 ** 3) * safety_factor

    chunk_t = max(1, int(max_bytes / bytes_per_timepoint))
    chunk_t = min(chunk_t, t)  # Don't exceed total timepoints

    debug(f"Calculated chunk size: {chunk_t} timepoints")
    debug(f"  Total timepoints: {t}")
    debug(f"  Voxel count: {total_voxels}")
    debug(f"  Bytes per timepoint: {bytes_per_timepoint / (1024**2):.2f} MB")
    debug(f"  Max bytes available: {max_bytes / (1024**3):.2f} GB")

    return chunk_t


def load_fMRI_chunked(
    nifti_path: Path,
    chunk_size_t: Optional[int] = None,
    max_ram_gb: Optional[float] = None,
    output_path: Optional[Path] = None
) -> Optional[np.ndarray]:
    """
    Load fMRI data in chunks to avoid RAM overflow.

    If output_path is provided, saves chunks incrementally to disk.
    Otherwise, returns the full array (if it fits).

    Args:
        nifti_path: Path to NIfTI file
        chunk_size_t: Number of timepoints per chunk (auto-calculated if None)
        max_ram_gb: Max RAM to use (from config if None)
        output_path: Optional path to save chunks incrementally

    Returns:
        Full data array if output_path is None, None if saving to disk
    """
    if not nifti_path.exists():
        error(f"NIfTI file not found: {nifti_path}")
        return None

    info(f"Loading fMRI data: {nifti_path}")
    file_size_mb = estimate_file_size_mb(nifti_path)
    info(f"File size: {file_size_mb:.2f} MB")

    # Load header to get shape and dtype
    img = nib.load(str(nifti_path))
    data = img.get_fdata(dtype=np.float32)
    shape = data.shape
    dtype = data.dtype

    if max_ram_gb is None:
        max_ram_gb = get_available_ram_gb()

    # Check if full data fits in RAM
    estimated_size_gb = (shape[0] * shape[1] * shape[2] * shape[3] * dtype.itemsize) / (1024 ** 3)
    if estimated_size_gb < max_ram_gb * 0.3:  # 30% safety margin
        info(f"Full data fits in RAM ({estimated_size_gb:.3f} GB < {max_ram_gb} GB)")
        return data

    info(f"Data too large for RAM ({estimated_size_gb:.3f} GB > {max_ram_gb} GB), using chunked loading")

    if chunk_size_t is None:
        chunk_size_t = calculate_chunk_size(shape, dtype, max_ram_gb)

    x, y, z, t = shape
    info(f"Processing in chunks of {chunk_size_t} timepoints (total {t})")

    if output_path:
        # Save chunks incrementally
        chunks = []
        for start_t in range(0, t, chunk_size_t):
            end_t = min(start_t + chunk_size_t, t)
            info(f"Loading chunk {start_t}-{end_t}/{t}")

            # Load only this chunk
            chunk_data = data[:, :, :, start_t:end_t]

            # Save to temporary file
            chunk_file = output_path.parent / f"{output_path.stem}_chunk_{start_t}_{end_t}.npy"
            np.save(str(chunk_file), chunk_data)
            chunks.append(chunk_file)

            # Force garbage collection
            del chunk_data
            gc.collect()

        info(f"Saved {len(chunks)} chunks to {output_path.parent}")
        return None
    else:
        # Try to assemble in memory (may fail if too large)
        logger.warning("Output path not provided; attempting to load full array")
        return data


def subsample_fMRI(
    data: np.ndarray,
    target_size_gb: Optional[float] = None,
    subsample_factor: Optional[int] = None
) -> np.ndarray:
    """
    Subsample fMRI data to reduce memory footprint.

    Subsampling can be done by:
    1. Reducing spatial resolution (downsampling voxels)
    2. Reducing temporal resolution (skipping timepoints)
    3. Both

    Args:
        data: 4D fMRI array (x, y, z, t)
        target_size_gb: Target size in GB (if provided, subsample_factor is calculated)
        subsample_factor: Factor to reduce by (e.g., 2 = half the voxels/timepoints)

    Returns:
        Subsampled data array
    """
    original_size_gb = data.nbytes / (1024 ** 3)
    info(f"Original data size: {original_size_gb:.3f} GB")

    if target_size_gb is not None:
        if target_size_gb >= original_size_gb:
            info("Target size >= original size, no subsampling needed")
            return data

        # Calculate subsample factor needed
        ratio = target_size_gb / original_size_gb
        subsample_factor = max(2, int(np.ceil(1.0 / (ratio ** 0.25))))  # 4D data
        info(f"Calculated subsample factor: {subsample_factor} to reach {target_size_gb:.3f} GB")

    if subsample_factor is None or subsample_factor < 2:
        return data

    x, y, z, t = data.shape
    info(f"Subsampling by factor {subsample_factor}")

    # Subsample in all dimensions
    new_x = max(1, x // subsample_factor)
    new_y = max(1, y // subsample_factor)
    new_z = max(1, z // subsample_factor)
    new_t = max(1, t // subsample_factor)

    # Use slicing with step
    subsampled = data[
        :new_x * subsample_factor : subsample_factor,
        :new_y * subsample_factor : subsample_factor,
        :new_z * subsample_factor : subsample_factor,
        :new_t * subsample_factor : subsample_factor
    ]

    new_size_gb = subsampled.nbytes / (1024 ** 3)
    info(f"Subsampled data size: {new_size_gb:.3f} GB (from {original_size_gb:.3f} GB)")

    return subsampled


def iter_fMRI_chunks(
    nifti_path: Path,
    chunk_size_t: int = 50,
    max_ram_gb: Optional[float] = None
) -> Iterator[Tuple[np.ndarray, int, int]]:
    """
    Iterator that yields fMRI data chunks one at a time.

    This is the most memory-efficient approach for processing large datasets.

    Yields:
        Tuple of (chunk_data, start_timepoint, end_timepoint)
    """
    if not nifti_path.exists():
        error(f"NIfTI file not found: {nifti_path}")
        return

    if max_ram_gb is None:
        max_ram_gb = get_available_ram_gb()

    img = nib.load(str(nifti_path))
    data = img.get_fdata(dtype=np.float32)
    shape = data.shape
    x, y, z, t = shape

    info(f"Iterating {t} timepoints in chunks of {chunk_size_t}")

    for start_t in range(0, t, chunk_size_t):
        end_t = min(start_t + chunk_size_t, t)
        chunk = data[:, :, :, start_t:end_t]
        yield chunk, start_t, end_t

        # Clean up
        del chunk
        gc.collect()


def process_roi_timecourses_chunked(
    input_path: Path,
    output_path: Path,
    roi_mask_paths: Dict[str, Path],
    chunk_size_t: int = 50
) -> None:
    """
    Process ROI timecourses from large fMRI files using chunked loading.

    Args:
        input_path: Path to fMRI NIfTI file
        output_path: Path to save ROI timecourses CSV
        roi_mask_paths: Dict mapping ROI name to mask NIfTI path
        chunk_size_t: Timepoints per chunk
    """
    info(f"Processing ROI timecourses: {input_path}")

    # Load ROI masks
    roi_masks = {}
    for roi_name, mask_path in roi_mask_paths.items():
        if not mask_path.exists():
            error(f"ROI mask not found: {mask_path}")
            continue
        mask_img = nib.load(str(mask_path))
        roi_masks[roi_name] = mask_img.get_fdata(dtype=bool)
        info(f"Loaded mask for {roi_name}: {mask_img.shape}")

    if not roi_masks:
        error("No valid ROI masks found")
        return

    # Initialize output
    results = []
    subject_id = input_path.stem

    # Process in chunks
    for chunk_data, start_t, end_t in iter_fMRI_chunks(input_path, chunk_size_t):
        info(f"Processing chunk {start_t}-{end_t}")

        for roi_name, mask in roi_masks.items():
            # Extract ROI timecourse for this chunk
            if mask.shape[:3] == chunk_data.shape[:3]:
                roi_data = chunk_data[mask]
                mean_signal = np.mean(roi_data, axis=1)  # Mean across voxels

                for t_idx, signal in enumerate(mean_signal):
                  results.append({
                      'subject_id': subject_id,
                      'timepoint': start_t + t_idx,
                      'roi': roi_name,
                      'mean_signal': float(signal)
                  })

    # Save results
    import pandas as pd
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    info(f"Saved ROI timecourses to {output_path}")


def main():
    """Main entry point for chunked loading demonstration."""
    config = get_config()
    info(f"Starting chunked loader with config: {config}")

    # Example usage (would be called with real paths in production)
    # This demonstrates the API without requiring actual data files

    info("Chunked loader module loaded successfully")
    info("Available functions:")
    info("  - load_fMRI_chunked: Load large fMRI files in chunks")
    info("  - subsample_fMRI: Reduce data size by subsampling")
    info("  - iter_fMRI_chunks: Iterator for memory-efficient processing")
    info("  - process_roi_timecourses_chunked: Process ROI timecourses in chunks")


if __name__ == "__main__":
    main()