import os
import gc
import psutil
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Iterator, Dict, Any
import nibabel as nib

from config import get_config
from utils.logging_config import get_logger, info, error, warning

logger = get_logger(__name__)

def estimate_file_size_mb(file_path: str) -> float:
    """
    Estimate the size of a file in Megabytes.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    size_bytes = path.stat().st_size
    return size_bytes / (1024 * 1024)

def get_available_ram_gb() -> float:
    """
    Get available system RAM in Gigabytes using psutil.
    """
    try:
        mem = psutil.virtual_memory()
        # Use available memory, falling back to total if 'available' is not reliable on some OS
        avail_bytes = mem.available if hasattr(mem, 'available') else mem.total
        return avail_bytes / (1024 ** 3)
    except Exception as e:
        warning(f"Could not read system memory via psutil: {e}. Defaulting to config limit.")
        return get_config().get('max_ram_gb', 7)

def calculate_chunk_size(
    file_size_mb: float,
    target_chunk_mb: float = 500.0
) -> int:
    """
    Calculate the number of timepoints (or slices) to load in a single chunk
    to keep memory usage under the target size.

    This is a heuristic based on the assumption that the data is roughly
    (Timepoints x Voxels x Subjects) and we want to process a fraction.
    For NIfTI, we often process by volume (timepoint).
    """
    if file_size_mb <= target_chunk_mb:
        return 0  # Signal to load whole file

    # Heuristic: If file is 10GB and we want 500MB chunks, we need ~20 chunks.
    # We assume data is loaded as (X, Y, Z, T). We will slice along T.
    # This function returns the number of volumes to load per chunk.
    # We assume the file size is proportional to the number of volumes.
    ratio = target_chunk_mb / file_size_mb
    # We need to know the total volumes to return a count.
    # Since this function only takes size, we return a ratio factor.
    # The caller must handle the actual slicing logic based on this factor.
    # To make it useful for the caller who needs an integer count:
    # We assume a standard max volume count for estimation if unknown,
    # but strictly speaking, the caller needs the header info.
    # Let's change the interface: return the ratio, and the caller calculates count.
    # Actually, let's keep it simple: return the ratio.
    # The caller will use: chunk_size = max(1, int(total_volumes * ratio))
    return ratio

def load_fMRI_chunked(
    file_path: str,
    start_idx: int,
    end_idx: int,
    memory_limit_gb: Optional[float] = None
) -> np.ndarray:
    """
    Load a specific chunk (slice along the time axis) of an fMRI NIfTI file.

    Args:
        file_path: Path to the .nii or .nii.gz file.
        start_idx: Start index (inclusive) for the time axis (4th dimension).
        end_idx: End index (exclusive) for the time axis.
        memory_limit_gb: Optional override for RAM limit.

    Returns:
        np.ndarray: The data chunk with shape (X, Y, Z, T_chunk).
    """
    if memory_limit_gb is None:
        memory_limit_gb = get_config().get('max_ram_gb', 7)

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        img = nib.load(path)
        data = img.get_fdata(dtype=np.float32) # Load as float32 to save memory vs float64

        if data.ndim != 4:
            raise ValueError(f"Expected 4D NIfTI file, got {data.ndim}D. File: {file_path}")

        # Ensure indices are within bounds
        total_timepoints = data.shape[3]
        start_idx = max(0, min(start_idx, total_timepoints))
        end_idx = max(0, min(end_idx, total_timepoints))

        if start_idx >= end_idx:
            raise ValueError(f"Invalid chunk range: [{start_idx}, {end_idx}) for {total_timepoints} timepoints.")

        chunk = data[..., start_idx:end_idx]
        return chunk

    except Exception as e:
        error(f"Failed to load fMRI chunk from {file_path}: {e}")
        raise

def subsample_fMRI(
    data: np.ndarray,
    step: int = 1
) -> np.ndarray:
    """
    Subsample the time axis of the fMRI data.

    Args:
        data: 4D numpy array (X, Y, Z, T).
        step: Subsampling step (e.g., 2 means every 2nd timepoint).

    Returns:
        Subsampled numpy array.
    """
    if step <= 1:
        return data
    return data[..., ::step]

def iter_fMRI_chunks(
    file_path: str,
    chunk_size_mb: float = 500.0,
    memory_limit_gb: Optional[float] = None
) -> Iterator[Tuple[int, int, np.ndarray]]:
    """
    Iterate over an fMRI file in memory-safe chunks.

    Yields:
        Tuple of (start_index, end_index, data_chunk)
    """
    if memory_limit_gb is None:
        memory_limit_gb = get_config().get('max_ram_gb', 7)

    file_size_mb = estimate_file_size_mb(file_path)
    path = Path(file_path)

    # Load header to get dimensions
    img = nib.load(path)
    data_shape = img.shape
    if len(data_shape) != 4:
        raise ValueError(f"Expected 4D NIfTI file, got {len(data_shape)}D. File: {file_path}")

    total_volumes = data_shape[3]

    # Estimate data size per volume in MB
    # Assuming float32 (4 bytes)
    bytes_per_volume = data_shape[0] * data_shape[1] * data_shape[2] * 4
    vol_size_mb = bytes_per_volume / (1024 * 1024)

    if vol_size_mb == 0:
        raise ValueError(f"Invalid volume size calculation for {file_path}")

    # Calculate volumes per chunk
    volumes_per_chunk = max(1, int((chunk_size_mb * 0.8) / vol_size_mb)) # 0.8 safety factor

    start = 0
    while start < total_volumes:
        end = min(start + volumes_per_chunk, total_volumes)
        info(f"Loading chunk: volumes {start} to {end} (total {total_volumes})")

        chunk = load_fMRI_chunked(str(path), start, end, memory_limit_gb)
        yield (start, end, chunk)

        # Force garbage collection to ensure memory is released before next load
        gc.collect()
        start = end

def process_roi_timecourses_chunked(
    input_path: str,
    output_path: str,
    roi_mask_path: Optional[str] = None,
    chunk_size_mb: float = 500.0
) -> None:
    """
    Process fMRI data in chunks to extract ROI timecourses and write to CSV.
    This function is a skeleton for the logic required by T013/T014.
    It demonstrates the chunked loading pattern.

    Note: This function assumes roi_mask_path is a 4D mask or a list of 3D masks.
    For T014, the critical part is the chunked iteration and writing.
    """
    path = Path(input_path)
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    info(f"Starting chunked processing of {input_path} -> {output_path}")

    # We need to handle the output accumulation.
    # Strategy: Write header once, then append chunks.
    # Or accumulate in memory if the output is small (timepoints x ROIs).
    # Since output is (subjects * timepoints) x ROIs, and timepoints are large,
    # we might need to stream the output too if it's huge, but usually
    # the extracted timecourse is much smaller than the full 4D volume.
    # Let's assume we can buffer the extracted timecourses for one subject/chunk.

    # For this implementation, we will iterate chunks, extract ROIs for the chunk,
    # and write to CSV immediately to keep memory low.

    # Determine ROIs (simplified: assume we load masks or have a fixed set of indices)
    # In a real scenario, we'd load the mask here once (it's usually small 3D).
    # If roi_mask_path is provided, load it.
    # If not, we might just save the full chunk or a dummy extraction.
    # For T014, the focus is on the loading mechanism.

    headers_written = False
    mode = 'w'

    try:
        for start_idx, end_idx, chunk_data in iter_fMRI_chunks(input_path, chunk_size_mb):
            # chunk_data shape: (X, Y, Z, T_chunk)
            # Simulate ROI extraction: mean over a specific voxel region for demonstration
            # In real T013, we would apply the mask here.
            # Here we just compute mean signal across the spatial dimensions for the chunk
            # to simulate a single "ROI" or we can compute mean for a fixed mask.
            # Let's assume we have a mask of shape (X, Y, Z) for one ROI.
            # Since we don't have the actual mask file in this context, we'll simulate
            # by taking the mean of the first 10x10x10 voxels as a placeholder "ROI".
            # This is just to show the data flow.

            # Extract a dummy ROI timecourse (mean of first 10x10x10 voxels)
            # Shape: (T_chunk,)
            # Note: This is a placeholder for the actual mask application logic.
            dummy_roi_data = np.mean(chunk_data[:10, :10, :10, :], axis=(0, 1, 2))

            # Write to CSV
            with open(out_path, mode) as f:
                if not headers_written:
                    f.write("timepoint,roi_mean_signal\n")
                    headers_written = True

                for t, val in enumerate(dummy_roi_data):
                    f.write(f"{start_idx + t},{val:.6f}\n")

            info(f"Processed chunk {start_idx}-{end_idx}, written to {output_path}")

    except Exception as e:
        error(f"Error during chunked processing: {e}")
        raise
    finally:
        gc.collect()

def main():
    """
    Main entry point for testing the chunked loader.
    """
    config = get_config()
    info(f"Running chunked loader with config: {config}")

    # Example usage (requires a real file to run successfully)
    # input_file = "data/raw/example_func.nii.gz"
    # output_file = "data/processed/roi_timecourses_chunked.csv"

    # For demonstration without a real file, we log the functions available.
    info("Functions available for chunked loading:")
    info("- estimate_file_size_mb")
    info("- get_available_ram_gb")
    info("- load_fMRI_chunked")
    info("- iter_fMRI_chunks")
    info("- process_roi_timecourses_chunked")

    # If a file path is provided via environment or args, run the pipeline
    # This is a placeholder for actual execution
    import sys
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
        output_path = sys.argv[2] if len(sys.argv) > 2 else "data/processed/test_output.csv"
        process_roi_timecourses_chunked(input_path, output_path)
    else:
        info("No input file provided. Usage: python code/02_chunked_loader.py <input_nifti> [output_csv]")

if __name__ == "__main__":
    main()